"""스케줄러 (PLAN §5/§6) — 매일 정해진 시각에 일일 파이프라인 실행.

APScheduler 블로킹 스케줄러. 단일 프로세스/VPS용 MVP.
기본 07:00(Asia/Seoul). 환경변수 BRIEF_HOUR/BRIEF_MINUTE로 조정.

실행: python -m econ_brief.scheduler
"""
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from econ_brief import daily
from econ_brief.util import ops_notify

HOUR = int(os.environ.get("BRIEF_HOUR", "7"))
MINUTE = int(os.environ.get("BRIEF_MINUTE", "0"))
TZ = "Asia/Seoul"


def job():
    print(f"\n[scheduler] 일일 파이프라인 시작")
    try:
        daily.run(send=True)
    except Exception as e:  # noqa: BLE001  (daily가 이미 ops_notify 하지만 안전망)
        ops_notify(f"스케줄 실행 실패: {type(e).__name__} — {e}")
        print(f"[scheduler] 실패: {e}")


def build_scheduler() -> BlockingScheduler:
    sched = BlockingScheduler(timezone=TZ)
    sched.add_job(job, CronTrigger(hour=HOUR, minute=MINUTE, timezone=TZ),
                  id="daily_brief", name="econ-brief daily")
    return sched


def main():
    sched = build_scheduler()
    nxt = sched.get_job("daily_brief")
    print(f"⏰ 스케줄러 시작 — 매일 {HOUR:02d}:{MINUTE:02d} {TZ} 실행")
    print(f"   등록 작업: {nxt.name} ({nxt.trigger})")
    print("   (Ctrl+C로 종료)")
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n스케줄러 종료.")


if __name__ == "__main__":
    main()
