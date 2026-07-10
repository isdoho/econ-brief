"""econ-brief — '맛보기' 일일 브리핑 프로토타입.

검증된 세 소스(ECOS·FRED·KIS)에서 라이브 데이터를 모아 →
Gemini로 P1(영끌러) 관점의 '오늘의 경제 브리핑' 1건을 생성한다.
DB·스케줄 없이 개념 증명만 한다.
"""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))                                  # verify_data_sources
sys.path.insert(0, "/Users/jinyoungyoon/Desktop/gray_stock_automation")  # kis 패키지

import requests                                                   # noqa: E402
from verify_data_sources import fred_latest, ecos_get, keys       # noqa: E402
from kis.client import KISClient                                  # noqa: E402
from kis.quote import Quote                                       # noqa: E402

GEMINI_KEY = keys["GEMINI_API_KEY"]
MODELS = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"]

_RANGE = {"D": ("20000101", "20991231"), "M": ("200001", "209912")}


def ecos_rows(stat, cycle, item):
    """(TIME, float) 오름차순 리스트."""
    start, end = _RANGE[cycle]
    j = ecos_get("StatisticSearch", 1, 100000, stat, cycle, start, end, item)
    rows = [(r["TIME"], float(r["DATA_VALUE"]))
            for r in j["StatisticSearch"]["row"] if r["DATA_VALUE"] not in ("", None)]
    return rows


def ecos_last_change(stat, cycle, item):
    """최신값, 직전대비 변화."""
    rows = ecos_rows(stat, cycle, item)
    (t, v), (_, p) = rows[-1], rows[-2]
    return t, v, v - p


def collect():
    """브리핑에 넣을 라이브 데이터를 모은다."""
    d = {}

    # --- 한국(ECOS) ---
    _, base, _ = ecos_last_change("722Y001", "D", "0101000")
    d["기준금리"] = base
    fxt, fx, fxd = ecos_last_change("731Y001", "D", "0000001")
    d["원달러"], d["원달러_전일대비"], d["환율일자"] = fx, fxd, fxt
    _, b3, b3d = ecos_last_change("817Y002", "D", "010200000")
    d["국고채3년"], d["국고채3년_전일대비"] = b3, b3d
    _, cd, cdd = ecos_last_change("817Y002", "D", "010502000")
    d["CD91일"], d["CD91일_전일대비"] = cd, cdd
    cpi = ecos_rows("901Y009", "M", "0")
    d["CPI월"], d["CPI지수"] = cpi[-1][0], cpi[-1][1]
    if len(cpi) > 12:
        d["CPI_전년비"] = round((cpi[-1][1] / cpi[-13][1] - 1) * 100, 1)

    # --- 미국(FRED) ---
    _, d["미국FFR"] = fred_latest("DFF")
    _, d["미국10년물"] = fred_latest("DGS10")

    # --- 증시(KIS) ---
    c = KISClient()
    q = Quote(c)
    for label, code in [("코스피", "0001"), ("코스닥", "1001")]:
        o = c.get("/uapi/domestic-stock/v1/quotations/inquire-index-price",
                  tr_id="FHPUP02100000",
                  params={"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": code})["output"]
        d[label] = o["bstp_nmix_prpr"]
        d[label + "_등락률"] = o["bstp_nmix_prdy_ctrt"]
    sam = q.current_price("005930")
    d["삼성전자"], d["삼성전자_등락률"] = sam["stck_prpr"], sam["prdy_ctrt"]
    return d


def build_prompt(d):
    data_lines = "\n".join(f"- {k}: {v}" for k, v in d.items())
    return f"""너는 경제를 잘 모르는 친구에게 카톡으로 설명하는, 친하고 똑똑한 형/누나야.
아래는 오늘 한국·미국의 핵심 경제 지표 실측치야. 이걸로 '오늘의 경제 브리핑'을 써줘.

[독자] 변동금리 대출(이른바 '영끌')을 가진 30대 직장인.
금리·환율·물가가 '내 대출이자와 생활비'에 무슨 의미인지 가장 궁금해해.

[작성 규칙]
- 전문용어 금지. 꼭 써야 하면 괄호로 쉽게 풀어줘.
- 정확히 아래 3블록, 각 제목은 굵게(**):
  1) **무슨 일이 있었나** — 핵심 사실 2~3줄
  2) **왜 그랬나** — 맥락 1~2줄
  3) **나에게 무슨 의미** — 대출이자·환율·물가가 내 지갑에 주는 영향 2~3줄
- 특정 종목·금융상품 매수/매도 추천 절대 금지. 정보·설명 톤만.
- 공포 조성·과장 금지. 숫자엔 항상 '그래서 무슨 뜻'을 붙여.
- 전체 300~400자 내외, 이모지 1~2개 허용.

[오늘의 데이터]
{data_lines}
"""


def gemini(prompt):
    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7}}
        r = requests.post(url, params={"key": GEMINI_KEY}, json=body, timeout=90)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        j = r.json()
        return model, j["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError("사용 가능한 Gemini 모델 없음")


def main():
    print("⏳ 라이브 데이터 수집 중 (ECOS·FRED·KIS)…")
    d = collect()
    print("\n📊 수집된 데이터")
    for k, v in d.items():
        print(f"   {k}: {v}")

    print("\n⏳ Gemini로 브리핑 생성 중…")
    model, text = gemini(build_prompt(d))

    print(f"\n{'━' * 60}")
    print(f"📈 오늘의 경제, 내 말로   (생성: {model})")
    print('━' * 60)
    print(text.strip())
    print('━' * 60)


if __name__ == "__main__":
    main()
