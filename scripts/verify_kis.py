"""econ-brief — KIS(한국투자증권) 시세 검증.

gray_stock_automation 의 검증된 `kis` 패키지를 그대로 재활용한다.
- 토큰 발급(캐시 우선) → 종목 현재가 → 지수(코스피/코스닥) 순으로 확인.
- 지수 조회는 quote.py에 없어 raw 엔드포인트(FHPUP02100000)로 직접 호출.
- 인증정보는 gray_stock_automation/.env 에서 로드(키 출력 안 함).
"""
import sys
from pathlib import Path

GSA = Path("/Users/jinyoungyoon/Desktop/gray_stock_automation")
sys.path.insert(0, str(GSA))

from kis.client import KISClient            # noqa: E402
from kis.quote import Quote                 # noqa: E402

OK, FAIL, WARN = "✅", "❌", "⚠️"


def show(o, *keys):
    """output dict에서 첫 존재 키의 값을, 없으면 None."""
    for k in keys:
        if k in o and o[k] not in ("", None):
            return o[k]
    return None


def main():
    c = KISClient()  # gray_stock_automation/.env 사용
    print(f"env={c.cfg.env}  base={c.cfg.base_url}\n")

    # 1) 토큰 ---------------------------------------------------------------
    try:
        t = c.token
        print(f"{OK} OAuth 토큰  ...{t.access_token[-8:]}  유효={t.is_valid()}  "
              f"(캐시 재사용 가능)")
    except Exception as e:
        print(f"{FAIL} 토큰 발급 실패: {type(e).__name__}: {e}")
        return

    # 2) 종목 현재가 --------------------------------------------------------
    print("\n[종목 현재가]")
    q = Quote(c)
    for name, code in [("삼성전자", "005930"), ("SK하이닉스", "000660")]:
        try:
            o = q.current_price(code)
            px = show(o, "stck_prpr")
            chg = show(o, "prdy_vrss")
            pct = show(o, "prdy_ctrt")
            print(f"  {OK} {name}({code})  {px}원  전일대비 {chg} ({pct}%)")
        except Exception as e:
            print(f"  {FAIL} {name}({code})  {type(e).__name__}: {e}")

    # 3) 지수 (코스피/코스닥/코스피200) ------------------------------------
    print("\n[지수]")
    for name, code in [("코스피", "0001"), ("코스닥", "1001"), ("코스피200", "2001")]:
        try:
            d = c.get(
                "/uapi/domestic-stock/v1/quotations/inquire-index-price",
                tr_id="FHPUP02100000",
                params={"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": code},
            )
            o = d.get("output", {})
            px = show(o, "bstp_nmix_prpr")
            chg = show(o, "bstp_nmix_prdy_vrss")
            pct = show(o, "bstp_nmix_prdy_ctrt", "prdy_ctrt")
            if px is None:
                print(f"  {WARN} {name}({code}) 응답 키 확인 필요 → {list(o)[:12]}")
            else:
                print(f"  {OK} {name}({code})  {px}  전일대비 {chg} ({pct}%)")
        except Exception as e:
            print(f"  {FAIL} {name}({code})  {type(e).__name__}: {e}")

    print()


if __name__ == "__main__":
    main()
