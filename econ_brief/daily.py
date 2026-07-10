"""일일 파이프라인 (W2 자동화) — 수집 → 브리핑 생성 → 발송을 한 번에.

PLAN §5 스케줄러(06:30)가 호출할 진입점. 발송 채널은 설정된 것만 시도하고,
자격증명이 없으면 건너뛴다(파이프라인은 실패하지 않음).

사용:
  python -m econ_brief.daily            # 수집+생성+발송(가능한 채널)
  python -m econ_brief.daily --no-send  # 수집+생성까지만
"""
import sys
from datetime import date as date_cls

from econ_brief import collector, composer, config
from econ_brief.util import ops_notify, retry


def _try_send(brief_date) -> list[str]:
    """설정된 채널로 발송 시도. 결과 메시지 리스트 반환."""
    msgs = []
    # Telegram (봇 토큰) — chat_id는 자동 탐색 가능
    if config.TELEGRAM_BOT_TOKEN:
        from econ_brief import telegram
        try:
            r = telegram.dispatch(brief_date)
            msgs.append(f"✅ Telegram 발송 → chat {r['chat_id']}")
        except Exception as e:
            msgs.append(f"❌ Telegram 발송 실패: {e}")
    # Slack (봇 토큰)
    if config.SLACK_BOT_TOKEN and config.SLACK_CHANNEL:
        from econ_brief import slack
        try:
            r = slack.dispatch(brief_date)
            msgs.append(f"✅ Slack 발송 → {r['channel']}")
        except Exception as e:
            msgs.append(f"❌ Slack 발송 실패: {e}")
    # 이메일 (Gmail SMTP)
    if config.SMTP_USER and config.SMTP_PASS:
        from econ_brief import dispatcher
        try:
            r = dispatcher.dispatch(brief_date)
            msgs.append(f"✅ 이메일 발송 → {r['to']}")
        except Exception as e:
            msgs.append(f"❌ 이메일 발송 실패: {e}")
    if not msgs:
        msgs.append("⏭  발송 건너뜀 — 설정된 채널 없음 (SLACK_* 또는 SMTP_* 필요)")
    return msgs


def run(send: bool = True, brief_date=None) -> dict:
    """수집→생성→발송. 각 단계 재시도, 실패 시 운영 알림 후 예외 전파(W5)."""
    brief_date = brief_date or date_cls.today()
    try:
        print("① 데이터 수집 → 적재")
        stats = retry(collector.collect, label="collect")
        print(f"   수집: 성공 {stats['ok']} · 실패 {stats['fail']} · {stats['rows']}행\n")

        print("② 브리핑 생성 → 저장")
        brief = retry(lambda: composer.compose(brief_date), label="compose")
        print(f"   briefing#{brief['id']} ({brief['date']} · {brief['model']})\n")
    except Exception as e:  # noqa: BLE001
        ops_notify(f"{brief_date} 파이프라인 실패: {type(e).__name__} — {e}")
        raise

    sent = []
    if send:
        print("③ 발송")
        sent = _try_send(brief_date)
        for m in sent:
            print(f"   {m}")
        if any(m.startswith("❌") for m in sent):
            ops_notify(f"{brief_date} 발송 일부 실패: {'; '.join(sent)}")

    return {"collected": stats, "briefing_id": brief["id"], "sent": sent}


def main():
    send = "--no-send" not in sys.argv
    print(f"━━ econ-brief 일일 파이프라인 ({date_cls.today()}) ━━\n")
    run(send=send)
    print("\n완료.")


if __name__ == "__main__":
    main()
