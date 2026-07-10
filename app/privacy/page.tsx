import type { Metadata } from "next";
import Link from "next/link";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "개인정보처리방침",
  description:
    "오늘의 경제, 내 말로 개인정보처리방침 — 수집하는 정보, 쿠키와 광고, 이용자의 권리 안내.",
  alternates: { canonical: "/privacy" },
  robots: { index: false, follow: true },
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-xl px-4 py-8">
      <nav className="mb-4 text-xs text-slate-400">
        <Link href="/" className="hover:underline">
          오늘의 경제, 내 말로
        </Link>
        {" › "}
        <span className="text-slate-600">개인정보처리방침</span>
      </nav>

      <h1 className="text-xl font-extrabold">개인정보처리방침</h1>

      <div className="mt-4 space-y-4 text-sm leading-relaxed text-slate-700">
        <p>
          오늘의 경제, 내 말로(이하 &ldquo;본 사이트&rdquo;)는 이용자의 개인정보를 소중히 여기며,
          관련 법령을 준수합니다. 본 방침은 본 사이트가 어떤 정보를 수집하고 어떻게 이용하는지
          설명합니다.
        </p>

        <h2 className="pt-2 text-base font-bold text-slate-900">1. 수집하는 정보</h2>
        <p>
          본 사이트는 회원가입 기능이 없으며, 이름·이메일 등 개인 식별 정보를 직접 수집하지
          않습니다. 서비스 운영 과정에서 접속 기록(IP 주소, 브라우저 종류, 방문 페이지 등)이
          호스팅 사업자 및 분석 도구를 통해 자동으로 수집될 수 있습니다.
        </p>

        <h2 className="pt-2 text-base font-bold text-slate-900">2. 쿠키와 광고</h2>
        <p>
          본 사이트는 Google AdSense 광고를 게재할 수 있습니다. Google을 포함한 제3자 광고
          사업자는 쿠키를 사용하여 이용자의 이전 방문 기록을 바탕으로 맞춤형 광고를 표시할 수
          있습니다. 이용자는{" "}
          <a href="https://adssettings.google.com" rel="noreferrer" className="underline">
            Google 광고 설정
          </a>
          에서 맞춤 광고를 해제할 수 있으며, 브라우저 설정을 통해 쿠키 저장을 거부할 수 있습니다.
          Google의 광고 쿠키 사용에 대한 자세한 내용은{" "}
          <a
            href="https://policies.google.com/technologies/ads?hl=ko"
            rel="noreferrer"
            className="underline"
          >
            Google 광고 정책
          </a>
          을 참고하세요.
        </p>

        <h2 className="pt-2 text-base font-bold text-slate-900">3. 정보의 보관과 제공</h2>
        <p>
          본 사이트는 수집된 접속 기록을 통계 및 서비스 개선 목적 외로 이용하지 않으며, 법령에
          따른 요청을 제외하고 제3자에게 제공하지 않습니다.
        </p>

        <h2 className="pt-2 text-base font-bold text-slate-900">4. 방침의 변경</h2>
        <p>
          본 방침은 법령 또는 서비스 변경에 따라 수정될 수 있으며, 변경 시 본 페이지에
          게시합니다.
        </p>

        <p className="text-xs text-slate-400">시행일: 2026년 7월 11일</p>
      </div>
    </main>
  );
}
