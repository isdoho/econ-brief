"""백필 — 과거 평일 날짜의 브리핑을 as-of 데이터로 생성해 아카이브를 채운다.

각 날짜에 대해 '그 날까지 관측된 데이터'만으로 변동을 계산하므로
수치는 정직한 과거값이다(미래 데이터 누수 없음). LLM 호출이 날짜당 1회 발생.

사용: python -m econ_brief.backfill --days 30   # 오늘 제외 과거 30일 중 평일
      python -m econ_brief.backfill --days 30 --force  # 기존 브리핑도 재생성
"""
import argparse
import time
from datetime import date as date_cls, timedelta

from econ_brief import composer, db


def backfill(days: int, force: bool = False, pause: float = 2.0) -> dict:
    today = date_cls.today()
    targets = [
        d for d in (today - timedelta(days=i) for i in range(days, 0, -1))
        if d.weekday() < 5  # 주말 제외 (일별 지표가 주말엔 갱신되지 않음)
    ]
    made, skipped, failed = [], [], []
    with db.connect() as conn:
        existing = {d for d in targets if db.get_briefing(conn, d)}
    for d in targets:
        if d in existing and not force:
            skipped.append(d)
            continue
        try:
            r = composer.compose(d, as_of=True)
            made.append(d)
            print(f"  ✅ {d}  briefing#{r['id']} ({r['model']})")
            time.sleep(pause)  # LLM 레이트리밋 여유
        except Exception as e:  # noqa: BLE001
            failed.append(d)
            print(f"  ❌ {d}  {type(e).__name__}: {e}")
    return {"made": made, "skipped": skipped, "failed": failed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="오늘 제외 과거 N일 (기본 30)")
    ap.add_argument("--force", action="store_true", help="기존 브리핑도 재생성")
    args = ap.parse_args()
    print(f"⏳ 백필 시작 — 과거 {args.days}일 평일\n")
    r = backfill(args.days, force=args.force)
    print(f"\n완료: 생성 {len(r['made'])} · 건너뜀 {len(r['skipped'])} · 실패 {len(r['failed'])}")
    if r["made"]:
        print("→ python -m econ_brief.export 로 JSON을 갱신하세요.")


if __name__ == "__main__":
    main()
