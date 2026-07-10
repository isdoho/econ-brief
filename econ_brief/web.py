"""웹 아카이브 (W3) — 브리핑 목록/상세 + 이메일 구독.

FastAPI. 브리핑은 briefings 테이블에서 읽어 렌더한다.
구독은 users/subscriptions에 적재(이중옵트인 메일 발송은 자격증명 준비 후 연결).

실행: uvicorn econ_brief.web:app --reload  (또는 python -m econ_brief.web)
"""
import html
import re
from datetime import date as date_cls

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from econ_brief import db

app = FastAPI(title="econ-brief 아카이브")

DISCLAIMER = "본 서비스는 정보 제공 목적이며 투자 결과에 책임지지 않습니다."

PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:0 auto;
   padding:28px 18px;color:#1d1d1f;line-height:1.7}}
 a{{color:#0a66c2;text-decoration:none}} a:hover{{text-decoration:underline}}
 h1{{font-size:22px}} .sub{{color:#888;font-size:13px;margin-bottom:24px}}
 .item{{padding:14px 0;border-bottom:1px solid #eee}}
 .date{{font-weight:600}} .snip{{color:#555;font-size:14px;margin-top:4px}}
 .brief b,.brief strong{{color:#111}}
 .foot{{margin-top:32px;font-size:12px;color:#aaa;border-top:1px solid #eee;padding-top:14px}}
 form{{margin:18px 0;display:flex;gap:8px}}
 input[type=email]{{flex:1;padding:9px;border:1px solid #ccc;border-radius:8px}}
 button{{padding:9px 16px;border:0;border-radius:8px;background:#0a66c2;color:#fff;cursor:pointer}}
</style></head><body>{body}
<div class="foot">{disclaimer}</div></body></html>"""


def _md(body_md: str) -> str:
    safe = html.escape(body_md)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    return safe.replace("\n", "<br>")


def _snippet(body_md: str, n: int = 80) -> str:
    plain = re.sub(r"\*\*", "", body_md).replace("\n", " ")
    return html.escape(plain[:n]) + ("…" if len(plain) > n else "")


@app.get("/", response_class=HTMLResponse)
def index():
    with db.connect() as conn:
        rows = db.list_briefings(conn)
    items = "".join(
        f'<div class="item"><a href="/b/{d}"><span class="date">{d}</span></a>'
        f'<div class="snip">{_snippet(body)}</div></div>'
        for (d, model, created, body) in rows
    ) or "<p>아직 브리핑이 없습니다.</p>"
    body = f"""<h1>📈 오늘의 경제, 내 말로</h1>
<div class="sub">매일 한·미 경제 지표를, 내 돈에 무슨 뜻인지로 풀어드려요.</div>
<form method="post" action="/subscribe">
  <input type="email" name="email" placeholder="이메일로 매일 받기" required>
  <button type="submit">구독</button>
</form>
{items}"""
    return PAGE.format(title="오늘의 경제, 내 말로", body=body, disclaimer=DISCLAIMER)


@app.get("/b/{d}", response_class=HTMLResponse)
def detail(d: str):
    try:
        bdate = date_cls.fromisoformat(d)
    except ValueError:
        raise HTTPException(404, "잘못된 날짜")
    with db.connect() as conn:
        row = db.get_briefing(conn, bdate)
    if not row:
        raise HTTPException(404, "브리핑 없음")
    _, body_md, model, created = row
    body = f"""<a href="/">← 목록</a>
<h1>📈 {bdate}</h1>
<div class="sub">생성 모델 {html.escape(model or '')} · {created:%Y-%m-%d %H:%M}</div>
<div class="brief">{_md(body_md)}</div>"""
    return PAGE.format(title=f"{bdate} 브리핑", body=body, disclaimer=DISCLAIMER)


@app.post("/subscribe")
def subscribe(email: str = Form(...)):
    with db.connect() as conn:
        db.add_subscriber(conn, email.strip().lower())
    # 이중옵트인 확인메일 발송은 발송 자격증명 연결 후(W2 발송 완료 시) 활성화.
    body = (f"<h1>거의 다 됐어요</h1><p><b>{html.escape(email)}</b> 구독 접수.</p>"
            f'<p style="color:#888">확인 메일 발송(이중옵트인)은 발송 채널 연결 후 활성화됩니다.</p>'
            f'<p><a href="/">← 목록으로</a></p>')
    return HTMLResponse(PAGE.format(title="구독 접수", body=body, disclaimer=DISCLAIMER))


@app.get("/api/briefings")
def api_briefings():
    with db.connect() as conn:
        rows = db.list_briefings(conn)
    return JSONResponse([
        {"date": str(d), "model": model, "created_at": created.isoformat(), "body_md": body}
        for (d, model, created, body) in rows
    ])


@app.get("/healthz")
def healthz():
    return {"ok": True}


def main():
    import uvicorn
    uvicorn.run("econ_brief.web:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
