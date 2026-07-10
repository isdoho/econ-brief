"""정적 export — briefings 테이블을 웹(Next.js 정적 사이트)용 JSON으로 내보낸다.

산출물: public/data/briefings.json
  {"updated_at": ISO8601, "briefings": [{date, model, created_at, body_md, payload}]}

기존 파일이 있으면 병합한다(같은 날짜는 DB가 우선). CI처럼 매번 빈 DB로
시작하는 환경에서도 과거 아카이브가 유실되지 않도록 하기 위함이다.

사용: python -m econ_brief.export
"""
import json
from pathlib import Path

from econ_brief import db
from econ_brief.config import ROOT

OUT_PATH = ROOT / "public" / "data" / "briefings.json"


def export(out_path: Path = OUT_PATH) -> dict:
    """DB의 브리핑을 기존 JSON과 병합해 파일로. 요약 통계 반환."""
    with db.connect() as conn:
        rows = db.list_briefings_full(conn)
    by_date = {}
    if out_path.exists():
        for b in json.loads(out_path.read_text(encoding="utf-8")).get("briefings", []):
            by_date[b["date"]] = b
    for (d, model, created, body_md, payload) in rows:
        by_date[str(d)] = {
            "date": str(d),
            "model": model,
            "created_at": created.isoformat(),
            "body_md": body_md,
            "payload": payload,  # jsonb → psycopg가 dict로 반환
        }
    briefings = sorted(by_date.values(), key=lambda b: b["date"], reverse=True)
    updated_at = max((b["created_at"] for b in briefings), default=None)
    doc = {"updated_at": updated_at, "briefings": briefings}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"count": len(briefings), "path": str(out_path)}


def main():
    r = export()
    print(f"✅ 브리핑 {r['count']}건 → {r['path']}")


if __name__ == "__main__":
    main()
