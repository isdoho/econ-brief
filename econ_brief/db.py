"""Postgres 접근 계층 — psycopg3.

W1에서 쓰는 것:
- indicator 등록(upsert) → id 회수
- indicator_values 시계열 적재(upsert)
- 최신값/직전대비 조회 (변동 계산용)
"""
from contextlib import contextmanager

import psycopg

from econ_brief.config import dsn


@contextmanager
def connect():
    conn = psycopg.connect(dsn())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def upsert_indicator(conn, source, series_code, item_code, cycle, name, unit) -> int:
    """indicators 한 행 보장 후 id 반환. 이름/단위는 최신값으로 갱신."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO indicators (source, series_code, item_code, cycle, name, unit)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, series_code, item_code)
            DO UPDATE SET name = EXCLUDED.name,
                          unit = EXCLUDED.unit,
                          cycle = EXCLUDED.cycle
            RETURNING id
            """,
            (source, series_code, item_code, cycle, name, unit),
        )
        return cur.fetchone()[0]


def upsert_values(conn, indicator_id: int, rows: list[tuple[str, float]]) -> int:
    """(ts, value) 다건 upsert. 반영 행수 반환."""
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO indicator_values (indicator_id, ts, value)
            VALUES (%s, %s, %s)
            ON CONFLICT (indicator_id, ts)
            DO UPDATE SET value = EXCLUDED.value
            """,
            [(indicator_id, ts, val) for ts, val in rows],
        )
    return len(rows)


def latest_two(conn, indicator_id: int) -> list[tuple[str, float]]:
    """최신 2개 관측치 (ts, value), 최신이 먼저. 변동 계산용."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ts, value FROM indicator_values
            WHERE indicator_id = %s
            ORDER BY ts DESC
            LIMIT 2
            """,
            (indicator_id,),
        )
        return [(ts, float(v)) for ts, v in cur.fetchall()]


def latest_two_asof(conn, indicator_id: int, cutoff_ts: str) -> list[tuple[str, float]]:
    """cutoff_ts 이하 최신 2개 관측치. 백필용 — cutoff는 해당 지표 ts 포맷과 동일해야 함."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ts, value FROM indicator_values
            WHERE indicator_id = %s AND ts <= %s
            ORDER BY ts DESC
            LIMIT 2
            """,
            (indicator_id, cutoff_ts),
        )
        return [(ts, float(v)) for ts, v in cur.fetchall()]


def upsert_briefing(conn, date, payload_json: str, body_md: str, model: str) -> int:
    """날짜별 브리핑 1건 보장(있으면 갱신). id 반환."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO briefings (date, payload_json, body_md, model)
            VALUES (%s, %s::jsonb, %s, %s)
            ON CONFLICT (date)
            DO UPDATE SET payload_json = EXCLUDED.payload_json,
                          body_md = EXCLUDED.body_md,
                          model = EXCLUDED.model,
                          created_at = now()
            RETURNING id
            """,
            (date, payload_json, body_md, model),
        )
        return cur.fetchone()[0]


def get_briefing(conn, date) -> tuple | None:
    """(date, body_md, model, created_at) 반환."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT date, body_md, model, created_at FROM briefings WHERE date = %s",
            (date,),
        )
        return cur.fetchone()


def list_briefings(conn, limit: int = 60) -> list[tuple]:
    """(date, model, created_at, body_md) 최신순. 아카이브 목록용."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT date, model, created_at, body_md FROM briefings "
            "ORDER BY date DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


def list_briefings_full(conn) -> list[tuple]:
    """(date, model, created_at, body_md, payload_json) 최신순 전체. 정적 export용."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT date, model, created_at, body_md, payload_json FROM briefings "
            "ORDER BY date DESC"
        )
        return cur.fetchall()


def add_subscriber(conn, email: str, channel: str = "email") -> int:
    """구독자 upsert(이메일 유니크). id 반환. (W3 이중옵트인 검증은 verified_at으로)"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, channel) VALUES (%s, %s)
            ON CONFLICT (email) DO UPDATE SET channel = EXCLUDED.channel
            RETURNING id
            """,
            (email, channel),
        )
        uid = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO subscriptions (user_id, type) VALUES (%s, 'daily_brief') "
            "ON CONFLICT DO NOTHING",
            (uid,),
        )
        return uid


def add_loan_profile(conn, user_id, kind, balance, benchmark, spread, current_rate) -> int:
    """대출 프로필 생성. id 반환."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO loan_profiles (user_id, kind, balance, benchmark, spread, current_rate)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (user_id, kind, balance, benchmark, spread, current_rate),
        )
        return cur.fetchone()[0]


def list_loan_profiles(conn) -> list[tuple]:
    """(id, user_id, kind, balance, benchmark, spread, current_rate) 전체."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, user_id, kind, balance, benchmark, spread, current_rate "
            "FROM loan_profiles ORDER BY id"
        )
        return cur.fetchall()


def update_profile_rate(conn, profile_id: int, new_rate: float) -> None:
    """알림 후 프로필 현재금리를 갱신(다음 변동 비교 기준)."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE loan_profiles SET current_rate = %s, updated_at = now() WHERE id = %s",
            (new_rate, profile_id),
        )


def record_alert(conn, user_id, alert_type, payload_json: str) -> int:
    """알림 이력 적재. id 반환."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO alerts (user_id, type, payload_json, sent_at) "
            "VALUES (%s, %s, %s::jsonb, now()) RETURNING id",
            (user_id, alert_type, payload_json),
        )
        return cur.fetchone()[0]


def benchmark_latest_two(conn, source, series_code, item_code) -> list[tuple]:
    """벤치마크 지표의 최신 2개 (ts, value). 변동 감지용."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT iv.ts, iv.value
            FROM indicator_values iv
            JOIN indicators i ON i.id = iv.indicator_id
            WHERE i.source = %s AND i.series_code = %s AND i.item_code = %s
            ORDER BY iv.ts DESC LIMIT 2
            """,
            (source, series_code, item_code),
        )
        return [(ts, float(v)) for ts, v in cur.fetchall()]


def all_indicators(conn) -> list[tuple]:
    """(id, source, series_code, item_code, cycle, name, unit) 전체."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, source, series_code, item_code, cycle, name, unit "
            "FROM indicators ORDER BY id"
        )
        return cur.fetchall()
