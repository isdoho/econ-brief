"""FRED (미 연준) 클라이언트 — series_id로 관측치 시계열을 받는다."""
import requests

from econ_brief.config import FRED_API_KEY

URL = "https://api.stlouisfed.org/fred/series/observations"


def observations(series_id: str, limit: int = 120) -> list[tuple[str, float]]:
    """최근 limit개 관측치를 (date 'YYYY-MM-DD', value) 오름차순으로.

    결측치('.')는 건너뛴다. limit는 최신 기준이라 desc로 받아 뒤집는다.
    """
    p = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    r = requests.get(URL, params=p, timeout=30)
    r.raise_for_status()
    rows = []
    for o in r.json()["observations"]:
        if o["value"] not in (".", ""):
            rows.append((o["date"], float(o["value"])))
    rows.reverse()  # desc → asc
    return rows
