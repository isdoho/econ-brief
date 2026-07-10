import type { Metadata } from "next";
import Link from "next/link";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "사이트 소개",
  description:
    "오늘의 경제, 내 말로 — 한국은행 ECOS와 미 연준 FRED 공개 데이터를 바탕으로 매일 아침 경제 브리핑을 만드는 방법을 소개합니다.",
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-xl px-4 py-8">
      <nav className="mb-4 text-xs text-slate-400">
        <Link href="/" className="hover:underline">
          오늘의 경제, 내 말로
        </Link>
        {" › "}
        <span className="text-slate-600">사이트 소개</span>
      </nav>

      <h1 className="text-xl font-extrabold">사이트 소개</h1>

      <div className="mt-4 space-y-4 text-sm leading-relaxed text-slate-700">
        <p>
          <b>오늘의 경제, 내 말로</b>는 기준금리·환율·물가 같은 딱딱한 경제 지표를{" "}
          <b>&ldquo;그래서 내 대출이자랑 생활비에 무슨 뜻인데?&rdquo;</b> 관점으로 풀어주는 매일
          아침 경제 브리핑 아카이브입니다. 변동금리 대출을 가진 직장인이 출근길 1분 동안 읽을 수
          있는 분량을 목표로 합니다.
        </p>

        <h2 className="pt-2 text-base font-bold text-slate-900">브리핑이 만들어지는 과정</h2>
        <p>
          매일 아침 한국은행 경제통계시스템(ECOS)과 미국 연방준비제도 경제 데이터(FRED)의 공개
          API에서 기준금리, 원/달러 환율, 국고채·CD 금리, 소비자물가지수 등 핵심 지표를
          수집합니다. 전일(또는 전월) 대비 변동은 <b>코드가 계산</b>하고, AI는 그 숫자가 생활에
          어떤 의미인지 <b>설명만</b> 작성합니다. 숫자를 AI가 지어내지 않도록 역할을 분리한
          구조입니다.
        </p>

        <h2 className="pt-2 text-base font-bold text-slate-900">이용 시 유의사항</h2>
        <p>
          본 사이트의 모든 내용은 정보 제공 목적입니다. 특정 금융상품의 매수·매도 권유가 아니며,
          투자 판단에 따른 결과에 책임지지 않습니다. 지표 원본 수치는 한국은행 ECOS와 FRED에서
          직접 확인할 수 있습니다.
        </p>

        <h2 className="pt-2 text-base font-bold text-slate-900">문의</h2>
        <p>
          사이트에 대한 의견이나 제안은 이메일(
          <a href="mailto:gray.yoon@balancehero.com" className="underline">
            gray.yoon@balancehero.com
          </a>
          )로 보내주세요.
        </p>
      </div>
    </main>
  );
}
