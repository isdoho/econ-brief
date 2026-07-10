"""브리핑 생성기 (W2) — DB의 변동 데이터를 LLM으로 'P1 영끌러 브리핑'으로.

흐름: changes(DB) → 구조화 payload → Gemini(고정 3블록) → briefings 테이블 upsert.
숫자는 코드가 계산(changes), LLM은 '설명'만 한다(PLAN §14 리스크 대응).

사용: python -m econ_brief.composer
"""
import json
from datetime import date as date_cls

from econ_brief import changes, db
from econ_brief.llm import gemini

# 브리핑에 넣을 핵심 지표(레지스트리 이름 기준). 과다 정보 방지 위해 선별.
HEADLINE = [
    "기준금리", "원/달러 환율", "국고채 3년", "CD 91일",
    "소비자물가지수(CPI)", "미 실효 연방기금금리(일)", "미 10년물 국채",
]


def build_payload(conn, as_of=None) -> dict:
    """LLM 입력용 구조화 데이터. {지표: {value, delta, pct, ts, unit}}."""
    rows = {c["name"]: c for c in changes.all_changes(conn, as_of=as_of)}
    out = {}
    for name in HEADLINE:
        c = rows.get(name)
        if not c:
            continue
        out[name] = {
            "value": round(c["value"], 4),
            "delta": None if c["delta"] is None else round(c["delta"], 4),
            "pct": None if c["pct"] is None else round(c["pct"], 2),
            "ts": c["ts"],
            "unit": c["unit"],
        }
    return out


def build_prompt(payload: dict) -> str:
    lines = []
    for name, v in payload.items():
        chg = ""
        if v["delta"] is not None:
            chg = f"  (직전대비 {v['delta']:+g}, {v['pct']:+.2f}%)"
        lines.append(f"- {name}: {v['value']}{v['unit']}{chg}  [{v['ts']}]")
    data_block = "\n".join(lines)
    return f"""너는 경제를 잘 모르는 친구에게 카톡으로 설명하는, 친하고 똑똑한 형/누나야.
아래는 오늘 한국·미국의 핵심 경제 지표 실측치(직전대비 변동 포함)야.
이걸로 '오늘의 경제 브리핑'을 써줘.

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
{data_block}
"""


def compose(brief_date=None, as_of: bool = False) -> dict:
    """브리핑 1건 생성 후 DB 저장. 결과 요약 반환.

    as_of=True면 brief_date까지 관측된 데이터만으로 계산(과거 날짜 백필용).
    """
    brief_date = brief_date or date_cls.today()
    with db.connect() as conn:
        payload = build_payload(conn, as_of=brief_date if as_of else None)
        if not payload:
            raise RuntimeError("브리핑에 넣을 데이터 없음 — 먼저 collector를 실행하세요.")
        model, text = gemini(build_prompt(payload))
        body = text.strip()
        bid = db.upsert_briefing(conn, brief_date, json.dumps(payload, ensure_ascii=False),
                                 body, model)
    return {"id": bid, "date": str(brief_date), "model": model, "body": body}


def main():
    print("⏳ 브리핑 생성 중 (DB 변동데이터 → Gemini)…\n")
    r = compose()
    bar = "━" * 60
    print(bar)
    print(f"📈 오늘의 경제, 내 말로   ({r['date']} · {r['model']} · briefing#{r['id']})")
    print(bar)
    print(r["body"])
    print(bar)
    print("→ briefings 테이블에 저장됨.")


if __name__ == "__main__":
    main()
