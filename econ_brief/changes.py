"""'어제 vs 오늘' 변동 계산 — W1 완료 정의의 핵심.

적재된 시계열에서 각 지표의 최신값과 직전 관측 대비 변동을 뽑는다.
일별 지표는 사실상 '전영업일 대비', 월별 지표는 '전월 대비'가 된다.
"""
from datetime import date as date_cls

from econ_brief import db


def _cutoff_for(sample_ts: str, as_of: date_cls) -> str:
    """지표의 ts 원본 포맷(YYYYMMDD/YYYYMM/YYYY-MM-DD)에 맞춘 컷오프 문자열."""
    if "-" in sample_ts:
        return as_of.isoformat()
    if len(sample_ts) == 8:
        return as_of.strftime("%Y%m%d")
    if len(sample_ts) == 6:
        return as_of.strftime("%Y%m")
    return as_of.isoformat()


def change_for(conn, indicator_id: int, as_of: date_cls | None = None) -> dict | None:
    """최신값/직전대비 변동. 데이터가 1개뿐이거나 없으면 None/부분 반환.

    as_of를 주면 그 날짜까지 관측된 데이터 기준으로 계산(백필용).
    """
    two = db.latest_two(conn, indicator_id)
    if not two:
        return None
    if as_of is not None:
        two = db.latest_two_asof(conn, indicator_id, _cutoff_for(two[0][0], as_of))
        if not two:
            return None
    (ts, val) = two[0]
    if len(two) < 2:
        return {"ts": ts, "value": val, "prev": None, "delta": None, "pct": None}
    (_, prev) = two[1]
    delta = val - prev
    pct = (delta / prev * 100) if prev != 0 else None
    return {
        "ts": ts,
        "value": val,
        "prev": prev,
        "delta": delta,
        "pct": pct,
    }


def all_changes(conn, as_of: date_cls | None = None) -> list[dict]:
    """모든 지표의 변동을 메타와 함께."""
    out = []
    for (ind_id, source, series, item, cycle, name, unit) in db.all_indicators(conn):
        c = change_for(conn, ind_id, as_of=as_of)
        if c is None:
            continue
        out.append({"name": name, "source": source, "unit": unit, "cycle": cycle, **c})
    return out


def _fmt(c: dict) -> str:
    arrow = ""
    if c["delta"] is not None:
        if c["delta"] > 0:
            arrow = f"▲ +{c['delta']:.3g}"
        elif c["delta"] < 0:
            arrow = f"▼ {c['delta']:.3g}"
        else:
            arrow = "─ 0"
        if c["pct"] is not None:
            arrow += f" ({c['pct']:+.2f}%)"
    return arrow or "(직전값 없음)"


def main():
    with db.connect() as conn:
        changes = all_changes(conn)
    print(f"\n{'지표':<22}{'최신값':>12}  {'변동(직전대비)':<24}{'기준시점'}")
    print("─" * 78)
    for c in changes:
        print(f"{c['name']:<22}{c['value']:>12.4g}  {_fmt(c):<24}{c['ts']}  {c['unit']}")
    print("─" * 78)
    print(f"총 {len(changes)}개 지표")


if __name__ == "__main__":
    main()
