"""Slack 발송 (W2) — 봇 토큰으로 채널에 브리핑 게시.

준비물(.env):
  SLACK_BOT_TOKEN=xoxb-...   (봇 OAuth 토큰, chat:write 스코프 필요)
  SLACK_CHANNEL=#오늘의경제   (또는 채널 ID, 봇을 채널에 초대해 둘 것)

사용: python -m econ_brief.slack [YYYY-MM-DD]
"""
import sys
from datetime import date as date_cls

import requests

from econ_brief import config, db

API = "https://slack.com/api/chat.postMessage"
DISCLAIMER = "본 메시지는 정보 제공 목적이며 투자 결과에 책임지지 않습니다."


def _blocks(bdate, body_md: str) -> list:
    """Slack Block Kit — 제목 + 본문(mrkdwn) + 면책. **굵게**는 Slack mrkdwn *굵게*로."""
    import re

    body = re.sub(r"\*\*(.+?)\*\*", r"*\1*", body_md)
    return [
        {"type": "header",
         "text": {"type": "plain_text", "text": f"📈 오늘의 경제, 내 말로 — {bdate}", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": body}},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": DISCLAIMER}]},
    ]


def post(briefing) -> str:
    """(date, body_md, model, created_at)를 Slack 채널에 게시. 채널 반환."""
    if not (config.SLACK_BOT_TOKEN and config.SLACK_CHANNEL):
        raise RuntimeError(
            "SLACK_BOT_TOKEN/SLACK_CHANNEL 미설정. .env에 봇 토큰과 채널을 넣으세요.\n"
            "  (api.slack.com/apps → 봇 생성 → OAuth scopes에 chat:write → 채널에 봇 초대)"
        )
    bdate, body_md, model, _ = briefing
    payload = {
        "channel": config.SLACK_CHANNEL,
        "text": f"📈 오늘의 경제, 내 말로 — {bdate}",  # 알림/폴백용
        "blocks": _blocks(bdate, body_md),
    }
    r = requests.post(
        API,
        headers={"Authorization": f"Bearer {config.SLACK_BOT_TOKEN}",
                 "Content-Type": "application/json; charset=utf-8"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Slack API 오류: {j.get('error')}")
    return config.SLACK_CHANNEL


def dispatch(brief_date=None) -> dict:
    brief_date = brief_date or date_cls.today()
    with db.connect() as conn:
        briefing = db.get_briefing(conn, brief_date)
        if not briefing:
            raise RuntimeError(f"{brief_date} 브리핑 없음 — 먼저 composer를 실행하세요.")
        channel = post(briefing)
    return {"date": str(brief_date), "channel": channel}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    brief_date = date_cls.fromisoformat(arg) if arg else date_cls.today()
    print(f"⏳ {brief_date} 브리핑 Slack 발송 중…")
    r = dispatch(brief_date)
    print(f"✅ 발송 완료 → {r['channel']}")


if __name__ == "__main__":
    main()
