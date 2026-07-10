"""수집기 — 레지스트리의 모든 지표를 소스에서 받아 Postgres에 적재.

사용: python -m econ_brief.collector
"""
from econ_brief import db
from econ_brief.registry import INDICATORS
from econ_brief.sources import ecos, fred


def fetch(source: str, series_code: str, item_code: str, cycle: str):
    """소스별로 (ts, value) 오름차순 시계열을 반환."""
    if source == "ECOS":
        return ecos.rows(series_code, cycle, item_code)
    if source == "FRED":
        return fred.observations(series_code)
    raise ValueError(f"알 수 없는 소스: {source}")


def collect() -> dict:
    """레지스트리 전체 수집·적재. 요약 통계 반환."""
    ok, fail, total_rows = 0, 0, 0
    with db.connect() as conn:
        for source, series, item, cycle, name, unit in INDICATORS:
            try:
                rows = fetch(source, series, item, cycle)
                ind_id = db.upsert_indicator(conn, source, series, item, cycle, name, unit)
                n = db.upsert_values(conn, ind_id, rows)
                latest = rows[-1] if rows else ("—", None)
                total_rows += n
                ok += 1
                print(f"  ✅ {source:<4} {name:<18} {n:>5}행  최신 {latest[1]} ({latest[0]})")
            except Exception as e:
                fail += 1
                print(f"  ❌ {source:<4} {name:<18} {type(e).__name__}: {e}")
    return {"ok": ok, "fail": fail, "rows": total_rows}


def main():
    print("⏳ 수집 시작 (ECOS·FRED → Postgres)\n")
    s = collect()
    print(f"\n수집 완료: 성공 {s['ok']} · 실패 {s['fail']} · 적재 {s['rows']}행")


if __name__ == "__main__":
    main()
