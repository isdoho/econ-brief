"""대출 금리 알리미 (W4 / F2) — 벤치마크 변동 → 내 이자 영향 계산 → 설명.

PLAN §3 F2: 규칙 기반 계산(LLM 호출 최소화) + 설명 문장만 LLM.
- 숫자(새 금리·월이자 변화)는 코드가 계산한다.
- 벤치마크: CD·국고채는 ECOS(이미 적재됨). COFIX는 은행연합회 연동 필요(미구현 안내).

월 이자 변화는 잔액×Δ금리/12 (이자 부담의 직접 변화 — 만기 정보 불필요).
원리금 상환액 변화는 만기가 있어야 하므로 MVP는 이자 변화로 안내한다.

사용: python -m econ_brief.alerts          # 모든 프로필 점검
      python -m econ_brief.alerts --seed   # 데모 프로필 1건 생성 후 점검
"""
import json
import sys

from econ_brief import db
from econ_brief.llm import gemini

# 벤치마크 이름 → ECOS (series_code, item_code). COFIX는 외부.
BENCHMARK_MAP = {
    "CD": ("ECOS", "817Y002", "010502000"),
    "국고채": ("ECOS", "817Y002", "010200000"),
    "국고채3년": ("ECOS", "817Y002", "010200000"),
}


def benchmark_change(conn, benchmark: str):
    """(ts, latest, prev, delta) 또는 None. COFIX 등 미지원이면 예외."""
    if benchmark not in BENCHMARK_MAP:
        raise RuntimeError(
            f"벤치마크 '{benchmark}' 미지원 — CD/국고채만 ECOS로 가능. "
            f"COFIX는 은행연합회(portal.kfb.or.kr) 연동 필요(PLAN §4)."
        )
    src, series, item = BENCHMARK_MAP[benchmark]
    two = db.benchmark_latest_two(conn, src, series, item)
    if len(two) < 2:
        return None
    (ts, latest), (_, prev) = two
    return ts, latest, prev, latest - prev


def compute_impact(profile, new_benchmark: float) -> dict:
    """프로필+새 벤치마크 → 새 금리, 월 이자 변화."""
    pid, uid, kind, balance, benchmark, spread, current_rate = profile
    new_rate = new_benchmark + (spread or 0.0)
    rate_delta = new_rate - (current_rate or 0.0)
    # 월 이자 변화 = 잔액 × Δ금리(%) / 100 / 12
    monthly_interest_delta = (balance or 0) * rate_delta / 100 / 12
    return {
        "old_rate": current_rate,
        "new_rate": round(new_rate, 3),
        "rate_delta": round(rate_delta, 3),
        "monthly_interest_delta": round(monthly_interest_delta),
        "balance": balance,
        "benchmark": benchmark,
    }


def explain(impact: dict) -> str:
    """변화 설명 문장만 LLM으로(숫자는 고정). 실패 시 규칙 기반 폴백."""
    direction = "올라" if impact["rate_delta"] > 0 else "내려"
    amt = abs(impact["monthly_interest_delta"])
    prompt = f"""너는 경제를 잘 모르는 친구에게 카톡으로 설명하는 친한 형/누나야.
아래 사실만으로 변동금리 대출자에게 2~3줄로 쉽게 설명해줘.
- 추천·단정 금지, 공포 조성 금지, 숫자는 그대로 사용.
- 전문용어 쓰면 괄호로 풀어줘.

[사실]
- 대출 기준금리({impact['benchmark']})가 움직여서 내 금리가 {impact['old_rate']}% → {impact['new_rate']}%로 {direction}갈 전망.
- 그 결과 월 이자 부담이 약 {amt:,}원 {('증가' if impact['rate_delta']>0 else '감소')} 예상(잔액 {impact['balance']:,}원 기준).
"""
    try:
        _, text = gemini(prompt, temperature=0.6)
        return text.strip()
    except Exception:
        return (f"대출 기준금리({impact['benchmark']}) 변동으로 금리가 "
                f"{impact['old_rate']}% → {impact['new_rate']}%로 바뀔 전망이에요. "
                f"월 이자 부담이 약 {amt:,}원 {'늘' if impact['rate_delta']>0 else '줄'} 것으로 보여요.")


def check_all(seed: bool = False) -> list[dict]:
    out = []
    with db.connect() as conn:
        if seed:
            uid = db.add_subscriber(conn, "demo@econ-brief.local")
            db.add_loan_profile(conn, uid, "변동", 300_000_000, "CD", 1.5, 4.0)
            print("  🌱 데모 프로필 생성: 변동 3억 / CD+1.5%p / 현재 4.0%")
        profiles = db.list_loan_profiles(conn)
        if not profiles:
            print("  대출 프로필 없음 — --seed로 데모 생성 가능.")
            return out
        for p in profiles:
            pid, uid, kind, balance, benchmark, spread, current_rate = p
            try:
                ch = benchmark_change(conn, benchmark)
            except RuntimeError as e:
                print(f"  ⏭  profile#{pid}: {e}")
                continue
            if not ch:
                print(f"  profile#{pid}: 벤치마크 데이터 부족")
                continue
            ts, latest, prev, bdelta = ch
            impact = compute_impact(p, latest)
            text = explain(impact)
            payload = {"benchmark_ts": ts, "benchmark": latest, **impact}
            aid = db.record_alert(conn, uid, "loan_rate", json.dumps(payload, ensure_ascii=False))
            db.update_profile_rate(conn, pid, impact["new_rate"])
            out.append({"profile": pid, "alert": aid, "impact": impact, "text": text})
            sign = "+" if impact["rate_delta"] > 0 else ""
            print(f"\n  🔔 profile#{pid} (잔액 {balance:,}원, {benchmark}+{spread}%p)")
            print(f"     벤치마크 {prev}% → {latest}% ({ts}) | "
                  f"내 금리 {impact['old_rate']}% → {impact['new_rate']}% ({sign}{impact['rate_delta']}%p)")
            print(f"     월 이자 변화 ≈ {impact['monthly_interest_delta']:+,}원")
            print(f"     💬 {text}")
    return out


def main():
    seed = "--seed" in sys.argv
    print("⏳ 대출 알리미 점검…")
    check_all(seed=seed)
    print("\n완료.")


if __name__ == "__main__":
    main()
