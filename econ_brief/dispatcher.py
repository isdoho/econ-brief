"""발송기 (W2) — 저장된 브리핑을 Gmail SMTP로 이메일 발송.

표준 라이브러리(smtplib)만 사용. Gmail '앱 비밀번호'가 필요하다
(.env의 SMTP_USER / SMTP_PASS). 발송 후 deliveries 테이블에 이력 적재.

사용: python -m econ_brief.dispatcher [YYYY-MM-DD]
"""
import smtplib
import sys
from datetime import date as date_cls
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from econ_brief import config, db

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465  # SSL

DISCLAIMER = "본 메일은 정보 제공 목적이며 투자 결과에 책임지지 않습니다."


def _md_to_html(body_md: str) -> str:
    """**굵게**와 줄바꿈만 가벼운 HTML로. (본문은 3블록 마크다운)"""
    import re

    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body_md)
    html = html.replace("\n", "<br>")
    return f"""<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;
font-size:15px;line-height:1.7;max-width:560px;color:#222">
{html}
<hr style="border:none;border-top:1px solid #eee;margin:20px 0">
<p style="font-size:12px;color:#999">{DISCLAIMER}</p>
</div>"""


def send(briefing) -> None:
    """(date, body_md, model, created_at) 튜플을 메일로 발송."""
    if not (config.SMTP_USER and config.SMTP_PASS):
        raise RuntimeError(
            "SMTP_USER/SMTP_PASS 미설정. .env에 Gmail 계정과 앱 비밀번호를 넣으세요.\n"
            "  (Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호 발급)"
        )
    bdate, body_md, model, _ = briefing
    to_addr = config.MAIL_TO or config.SMTP_USER

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 오늘의 경제, 내 말로 — {bdate}"
    msg["From"] = config.SMTP_USER
    msg["To"] = to_addr
    msg.attach(MIMEText(body_md + "\n\n— " + DISCLAIMER, "plain", "utf-8"))
    msg.attach(MIMEText(_md_to_html(body_md), "html", "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.login(config.SMTP_USER, config.SMTP_PASS)
        s.sendmail(config.SMTP_USER, [to_addr], msg.as_string())
    return to_addr


def dispatch(brief_date=None) -> dict:
    brief_date = brief_date or date_cls.today()
    with db.connect() as conn:
        briefing = db.get_briefing(conn, brief_date)
        if not briefing:
            raise RuntimeError(f"{brief_date} 브리핑 없음 — 먼저 composer를 실행하세요.")
        to_addr = send(briefing)
    return {"date": str(brief_date), "to": to_addr}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    brief_date = date_cls.fromisoformat(arg) if arg else date_cls.today()
    print(f"⏳ {brief_date} 브리핑 발송 중…")
    r = dispatch(brief_date)
    print(f"✅ 발송 완료 → {r['to']}")


if __name__ == "__main__":
    main()
