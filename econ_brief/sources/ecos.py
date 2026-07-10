"""ECOS (한국은행) 클라이언트.

검증 스크립트(scripts/verify_data_sources.py)에서 확인된 호출 규칙을 그대로 따른다:
- 키가 URL path에 들어간다 → 화면 출력 금지.
- 월별(M)은 YYYYMM, 일별(D)은 YYYYMMDD로 기간을 보내야 함(섞으면 ERROR-101).
- 일별 시리즈는 행수 cap 주의 → 1/100000 전체 요청 후 최신 구간 사용.
"""
import requests

from econ_brief.config import ECOS_API_KEY

BASE = "https://ecos.bok.or.kr/api"

# 주기별 기간 포맷 (검증 스크립트와 동일)
RANGE = {
    "D": ("20000101", "20991231"),
    "M": ("200001", "209912"),
    "A": ("2000", "2099"),
    "Q": ("2000Q1", "2099Q4"),
}


def _get(service: str, *path) -> dict:
    url = f"{BASE}/{service}/{ECOS_API_KEY}/json/kr/" + "/".join(str(x) for x in path)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    j = r.json()
    if "RESULT" in j:  # 에러/무데이터
        res = j["RESULT"]
        raise RuntimeError(f"ECOS {res.get('CODE')}: {res.get('MESSAGE')}")
    return j


def rows(stat: str, cycle: str, item: str) -> list[tuple[str, float]]:
    """(TIME, value) 오름차순 리스트. ECOS TIME 원본 포맷(YYYYMMDD/YYYYMM) 유지."""
    start, end = RANGE[cycle]
    j = _get("StatisticSearch", 1, 100000, stat, cycle, start, end, item)
    out = []
    for r in j["StatisticSearch"]["row"]:
        if r["DATA_VALUE"] not in ("", None):
            out.append((r["TIME"], float(r["DATA_VALUE"])))
    return out


def meta(stat: str, cycle: str, item: str) -> dict:
    """단위/항목명 등 메타(최근 1행). 적재 시 unit 채우는 용도."""
    start, end = RANGE[cycle]
    j = _get("StatisticSearch", 1, 1, stat, cycle, start, end, item)
    row = j["StatisticSearch"]["row"][0]
    return {"unit": row.get("UNIT_NAME", ""), "name": row.get("ITEM_NAME1", "")}
