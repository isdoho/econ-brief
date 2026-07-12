import type { Metadata } from "next";
import Script from "next/script";
import { SITE_URL } from "@/lib/briefings";
import "./globals.css";

// 애드센스 승인 후 발급받은 클라이언트 ID를 .env 에 설정 (예: ca-pub-1234567890123456)
const ADSENSE_CLIENT = process.env.NEXT_PUBLIC_ADSENSE_CLIENT;
// 애널리틱스 — 설정된 것만 로드 (둘 다 미설정이면 아무것도 로드 안 함)
const GA_ID = process.env.NEXT_PUBLIC_GA_ID; // GA4 측정 ID (예: G-XXXXXXXXXX)
const CF_BEACON_TOKEN = process.env.NEXT_PUBLIC_CF_BEACON_TOKEN; // Cloudflare Web Analytics 토큰

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "오늘의 경제, 내 말로 — 매일 아침 경제 브리핑",
    template: "%s | 오늘의 경제, 내 말로",
  },
  description:
    "기준금리·환율·물가 같은 한국·미국 핵심 경제 지표를 매일 아침, 내 대출이자와 생활비에 무슨 뜻인지 쉬운 말로 풀어주는 경제 브리핑 아카이브.",
  keywords: ["경제 브리핑", "기준금리", "환율", "물가", "CD금리", "국고채", "대출이자", "경제 뉴스 요약"],
  alternates: {
    canonical: "/",
    types: { "application/rss+xml": [{ url: "/rss.xml", title: "오늘의 경제, 내 말로 — RSS" }] },
  },
  openGraph: {
    type: "website",
    locale: "ko_KR",
    siteName: "오늘의 경제, 내 말로",
    title: "오늘의 경제, 내 말로 — 매일 아침 경제 브리핑",
    description: "한·미 핵심 경제 지표를 내 지갑 기준으로 풀어주는 매일 브리핑.",
  },
  robots: { index: true, follow: true },
  verification: {
    // 구글 서치콘솔 · 네이버 서치어드바이저 인증 코드는 .env 에 설정
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION,
    other: process.env.NEXT_PUBLIC_NAVER_SITE_VERIFICATION
      ? { "naver-site-verification": process.env.NEXT_PUBLIC_NAVER_SITE_VERIFICATION }
      : undefined,
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body className="bg-slate-50 text-slate-900">
        {children}
        <footer className="mx-auto max-w-xl border-t border-slate-200 px-4 py-6 text-xs leading-relaxed text-slate-400">
          <p>
            데이터 출처: 한국은행 ECOS · 미 연준 FRED (공개 API) · 매일 아침 자동 갱신. 수치는
            코드가 계산하고 설명은 AI가 작성합니다. 본 사이트의 내용은 정보 제공 목적이며 투자
            권유가 아니고, 투자 결과에 책임지지 않습니다.
          </p>
          <p className="mt-2 flex gap-3">
            <a href="/about" className="underline">
              사이트 소개
            </a>
            <a href="/privacy" className="underline">
              개인정보처리방침
            </a>
          </p>
          <p className="mt-2">
            함께 보면 좋은 사이트 —{" "}
            <a href="https://cheongyak-alimi.vercel.app" className="underline">
              청약 알리미
            </a>
            {" · "}
            <a href="https://market-cap-board.netlify.app" className="underline">
              시총 리더보드
            </a>
          </p>
        </footer>
        {ADSENSE_CLIENT && (
          <Script
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ADSENSE_CLIENT}`}
            crossOrigin="anonymous"
            strategy="afterInteractive"
          />
        )}
        {GA_ID && (
          <>
            <Script
              async
              src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
              strategy="afterInteractive"
            />
            <Script id="ga4-init" strategy="afterInteractive">
              {`window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '${GA_ID}');`}
            </Script>
          </>
        )}
        {CF_BEACON_TOKEN && (
          <Script
            defer
            src="https://static.cloudflareinsights.com/beacon.min.js"
            data-cf-beacon={`{"token": "${CF_BEACON_TOKEN}"}`}
            strategy="afterInteractive"
          />
        )}
      </body>
    </html>
  );
}
