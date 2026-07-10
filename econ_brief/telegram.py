"""Telegram 발송 (W2) — 봇 토큰으로 브리핑을 채팅에 전송.

준비물(.env):
  TELEGRAM_BOT_TOKEN=123456:ABC...   (@BotFather로 생성)
  TELEGRAM_CHAT_ID=...               (비워두면 getUpdates로 자동 탐색)

chat_id 얻기: 봇에게 아무 메시지나 한 번 보낸 뒤 `resolve_chat_id()` 호출.

사용:
  python -m econ_brief.telegram --whoami     # chat_id 자동 탐색
  python -m econ_brief.telegram [YYYY-MM-DD]  # 브리핑 발송
"""
import html
import re
import sys
from datetime import date as date_cls

import requests

from econ_brief import config, db

DISCLAIMER = "본 메시지는 정보 제공 목적이며 투자 결과에 책임지지 않습니다."


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}"


def resolve_chat_id() -> str | None:
    """봇에게 온 최근 메시지에서 chat_id를 찾는다(여러 종류 업데이트 대응)."""
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 미설정.")
    r = requests.get(_api("getUpdates"), timeout=30)
    r.raise_for_status()
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Telegram API 오류: {j.get('description')}")
    for upd in reversed(j.get("result", [])):
        msg = upd.get("message") or upd.get("channel_post") or {}
        chat = msg.get("chat")
        if chat:
            return str(chat["id"])
    return None


def _format(bdate, body_md: str) -> str:
    """HTML parse_mode용. 특수문자 escape 후 **굵게** → <b>굵게</b>."""
    safe = html.escape(body_md)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    title = html.escape(f"📈 오늘의 경제, 내 말로 — {bdate}")
    return f"<b>{title}</b>\n\n{safe}\n\n<i>{html.escape(DISCLAIMER)}</i>"


def send(briefing, chat_id: str | None = None) -> str:
    """(date, body_md, model, created_at)를 텔레그램으로 전송. chat_id 반환."""
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN 미설정. @BotFather로 봇 만들고 .env에 토큰을 넣으세요."
        )
    chat_id = chat_id or config.TELEGRAM_CHAT_ID or resolve_chat_id()
    if not chat_id:
        raise RuntimeError(
            "chat_id를 찾을 수 없음 — 봇에게 메시지를 한 번 보낸 뒤 다시 시도하세요."
        )
    bdate, body_md, model, _ = briefing
    payload = {
        "chat_id": chat_id,
        "text": _format(bdate, body_md),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(_api("sendMessage"), json=payload, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Telegram API 오류: {j.get('description')}")
    return str(chat_id)


def dispatch(brief_date=None) -> dict:
    brief_date = brief_date or date_cls.today()
    with db.connect() as conn:
        briefing = db.get_briefing(conn, brief_date)
        if not briefing:
            raise RuntimeError(f"{brief_date} 브리핑 없음 — 먼저 composer를 실행하세요.")
        chat_id = send(briefing)
    return {"date": str(brief_date), "chat_id": chat_id}


def main():
    if "--whoami" in sys.argv:
        cid = resolve_chat_id()
        print(f"chat_id: {cid}" if cid else "chat_id 못 찾음 — 봇에게 메시지를 먼저 보내세요.")
        return
    arg = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    brief_date = date_cls.fromisoformat(arg) if arg else date_cls.today()
    print(f"⏳ {brief_date} 브리핑 Telegram 발송 중…")
    r = dispatch(brief_date)
    print(f"✅ 발송 완료 → chat {r['chat_id']}")


if __name__ == "__main__":
    main()
