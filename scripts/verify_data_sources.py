"""econ-brief — 데이터 소스 검증 (W1 첫 코드).

목적: 가진 키(FRED/ECOS)로 MVP에 필요한 지표가 실제로 받아지는지 확인하고,
아직 미확정인 ECOS 통계표/항목 코드(시장금리·환율·CPI·COFIX)를 '발견'한다.

- 표준 라이브러리 + requests 만 사용.
- API 키는 화면에 절대 출력하지 않는다(URL에 키가 들어가는 ECOS 특성상 주의).
"""
from pathlib import Path
import sys
import requests

# --- .env 로드 (의존성 없이 직접 파싱) ---------------------------------------
ENV = Path(__file__).resolve().parent.parent / ".env"
keys = {}
for line in ENV.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        keys[k.strip()] = v.strip()

FRED_API_KEY = keys.get("FRED_API_KEY", "")
ECOS_API_KEY = keys.get("ECOS_API_KEY", "")

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
ECOS = "https://ecos.bok.or.kr/api"

OK, FAIL, INFO = "✅", "❌", "🔎"


def hr(title):
    print(f"\n{'=' * 64}\n{title}\n{'-' * 64}")


# --- FRED -------------------------------------------------------------------
def fred_latest(series_id):
    """FRED 시리즈의 최신 관측치를 (date, value)로. 실패 시 예외."""
    p = {"series_id": series_id, "api_key": FRED_API_KEY,
         "file_type": "json", "sort_order": "desc", "limit": 5}
    r = requests.get(FRED_URL, params=p, timeout=30)
    r.raise_for_status()
    obs = r.json()["observations"]
    for o in obs:                       # 최신 중 값이 '.'(결측) 아닌 첫 행
        if o["value"] not in (".", ""):
            return o["date"], o["value"]
    raise ValueError("관측치 없음")


def check_fred():
    hr("PART A — FRED (미국 매크로 + 원/달러)")
    targets = {
        "FEDFUNDS": "미 연방기금금리(월)",
        "DFF": "미 실효FFR(일) — rate_portpolio 검증됨",
        "DGS10": "미 10년물 국채(일)",
        "CPIAUCSL": "미 CPI(월)",
        "UNRATE": "미 실업률(월)",
        "DEXKOUS": "원/달러(일) — rate_portpolio 검증됨",
        "KORCPIALLMINMEI": "한국 CPI(월) — rate_portpolio 검증됨",
    }
    locked = {}
    for sid, desc in targets.items():
        try:
            d, v = fred_latest(sid)
            print(f"  {OK} {sid:<18} {v:>12}   ({d})  {desc}")
            locked[sid] = (d, v)
        except Exception as e:
            print(f"  {FAIL} {sid:<18} {'—':>12}   {type(e).__name__}: {e}  {desc}")
    return locked


# --- ECOS 공통 --------------------------------------------------------------
def ecos_get(service, *path):
    """ECOS 호출. 키는 path에 들어가므로 결과만 반환(예외 시 메시지 전달)."""
    url = f"{ECOS}/{service}/{ECOS_API_KEY}/json/kr/" + "/".join(str(x) for x in path)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    j = r.json()
    if "RESULT" in j:                   # 에러/무데이터
        res = j["RESULT"]
        raise RuntimeError(f"{res.get('CODE')}: {res.get('MESSAGE')}")
    return j


# ECOS 요청 날짜는 주기별 포맷이 달라야 한다(월별에 YYYYMMDD 보내면 ERROR-101).
_ECOS_RANGE = {"D": ("20000101", "20991231"), "M": ("200001", "209912"),
               "A": ("2000", "2099"), "Q": ("2000Q1", "2099Q4")}


def ecos_latest(stat, cycle, item):
    """특정 통계표/항목의 최신값 (TIME, DATA_VALUE, UNIT_NAME). 전체를 받아 마지막 행."""
    start, end = _ECOS_RANGE[cycle]
    j = ecos_get("StatisticSearch", 1, 100000, stat, cycle, start, end, item)
    rows = [r for r in j["StatisticSearch"]["row"] if r["DATA_VALUE"] not in ("", None)]
    last = rows[-1]
    return last["TIME"], last["DATA_VALUE"], last.get("UNIT_NAME", ""), last.get("ITEM_NAME1", "")


def ecos_items(stat, limit=40):
    """통계표의 항목 목록(ITEM_CODE, ITEM_NAME, CYCLE)을 나열 → 정확한 코드 발견용."""
    j = ecos_get("StatisticItemList", 1, limit, stat)
    return j["StatisticItemList"]["row"]


def ecos_table_search(needles, limit=2000):
    """전체 통계표에서 이름에 needles(키워드)가 든 표를 찾는다 → COFIX 위치 발견용."""
    j = ecos_get("StatisticTableList", 1, limit)
    out = []
    for r in j["StatisticTableList"]["row"]:
        name = r.get("STAT_NAME", "")
        if any(n in name for n in needles):
            out.append((r.get("STAT_CODE"), name, r.get("CYCLE", "")))
    return out


# --- ECOS 체크 --------------------------------------------------------------
def check_ecos():
    hr("PART B — ECOS 직접확인 (최신값)")
    checks = [
        ("기준금리",      "722Y001", "D", "0101000"),
        ("원/달러 환율",  "731Y001", "D", "0000001"),
        ("CPI 총지수",    "901Y009", "M", "0"),
        ("국고채(3년)",   "817Y002", "D", "010200000"),
        ("CD(91일)",      "817Y002", "D", "010502000"),
        ("주담대평균(신규)", "121Y006", "M", None),  # 항목 다수 → 코드 미지정 시 첫 항목
    ]
    for label, stat, cycle, item in checks:
        try:
            if item is None:
                # 항목 코드 모르면 첫 유효 항목으로 한 건만 확인
                item = ecos_items(stat)[0]["ITEM_CODE"]
            t, v, u, nm = ecos_latest(stat, cycle, item)
            print(f"  {OK} {label:<14} {stat}/{item}/{cycle}  →  {v} {u}  ({t})")
        except Exception as e:
            print(f"  {FAIL} {label:<14} {stat}/{item}/{cycle}  →  {e}")

    hr("PART C — ECOS 발견 (미확정 코드: 시장금리·환율·CPI 항목 나열)")
    discover = {
        "817Y002": "시장금리(일별) — 국고채/CD/회사채/콜 등",
        "731Y001": "원/달러 등 환율(매매기준율)",
        "901Y009": "소비자물가지수(CPI)",
    }
    for stat, desc in discover.items():
        print(f"\n  {INFO} [{stat}] {desc}")
        try:
            items = ecos_items(stat)
            for it in items[:25]:
                print(f"       {it.get('ITEM_CODE',''):<12} {it.get('CYCLE',''):<3} "
                      f"{it.get('ITEM_NAME','')}")
            if len(items) > 25:
                print(f"       … (+{len(items) - 25} more)")
        except Exception as e:
            print(f"       {FAIL} 항목 조회 실패: {e}")

    hr("PART D — COFIX 위치 탐색 (F2 대출 알리미 핵심)")
    try:
        hits = ecos_table_search(["COFIX", "코픽스", "대출금리", "가중평균금리"])
        if hits:
            for code, name, cyc in hits[:30]:
                print(f"  {OK} {(code or ''):<10} {(cyc or '-'):<3} {name or ''}")
        else:
            print(f"  {FAIL} ECOS 통계표 이름에 COFIX/코픽스/대출 키워드 없음 "
                  f"→ 은행연합회(portal.kfb.or.kr) 데이터 필요할 수 있음")
    except Exception as e:
        print(f"  {FAIL} 통계표 검색 실패: {e}")


def main():
    print(f"FRED key: {'있음' if FRED_API_KEY else '없음'} | "
          f"ECOS key: {'있음' if ECOS_API_KEY else '없음'}")
    if not (FRED_API_KEY and ECOS_API_KEY):
        print("키가 없습니다. econ-brief/.env 확인 필요.")
        sys.exit(1)
    check_fred()
    check_ecos()
    print(f"\n{'=' * 64}\n검증 끝.\n")


if __name__ == "__main__":
    main()
