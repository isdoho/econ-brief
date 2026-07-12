import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  SITE_URL,
  formatDateKo,
  formatTs,
  getBriefing,
  loadBriefings,
  mdToHtml,
  snippet,
} from "@/lib/briefings";

export const dynamic = "force-static";

type Props = { params: Promise<{ date: string }> };

export function generateStaticParams() {
  return loadBriefings().briefings.map((b) => ({ date: b.date }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { date } = await params;
  const b = getBriefing(date);
  if (!b) return {};
  return {
    title: `${formatDateKo(date)} 경제 브리핑 — 기준금리·환율·물가`,
    description: snippet(b.body_md, 150),
    alternates: { canonical: `/b/${date}` },
  };
}

function fmtNum(v: number): string {
  return v.toLocaleString("ko-KR", { maximumFractionDigits: 4 });
}

function DeltaBadge({ delta, pct }: { delta: number | null; pct: number | null }) {
  if (delta === null) return <span className="text-slate-400">—</span>;
  if (delta === 0) return <span className="text-slate-400">변동 없음</span>;
  const up = delta > 0;
  return (
    <span className={up ? "font-semibold text-red-600" : "font-semibold text-blue-600"}>
      {up ? "▲" : "▼"} {fmtNum(Math.abs(delta))}
      {pct !== null && ` (${pct > 0 ? "+" : ""}${pct.toFixed(2)}%)`}
    </span>
  );
}

export default async function BriefingPage({ params }: Props) {
  const { date } = await params;
  const b = getBriefing(date);
  if (!b) notFound();

  const { briefings } = loadBriefings();
  const idx = briefings.findIndex((x) => x.date === date);
  const newer = idx > 0 ? briefings[idx - 1] : null;
  const older = idx < briefings.length - 1 ? briefings[idx + 1] : null;
  const indicators = Object.entries(b.payload ?? {});

  // 검색엔진용 구조화 데이터 (NewsArticle + 브레드크럼)
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "NewsArticle",
        headline: `${formatDateKo(b.date)} 경제 브리핑 — 기준금리·환율·물가`,
        description: snippet(b.body_md, 150),
        datePublished: b.created_at,
        dateModified: b.created_at,
        mainEntityOfPage: `${SITE_URL}/b/${b.date}`,
        author: {
          "@type": "Organization",
          name: "오늘의 경제, 내 말로",
          url: SITE_URL,
        },
        publisher: {
          "@type": "Organization",
          name: "오늘의 경제, 내 말로",
          url: SITE_URL,
        },
        inLanguage: "ko",
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "홈", item: SITE_URL },
          {
            "@type": "ListItem",
            position: 2,
            name: `${b.date} 경제 브리핑`,
            item: `${SITE_URL}/b/${b.date}`,
          },
        ],
      },
    ],
  };

  return (
    <main className="mx-auto max-w-xl px-4 py-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <nav className="mb-4 text-xs text-slate-400">
        <Link href="/" className="hover:underline">
          오늘의 경제, 내 말로
        </Link>
        {" › "}
        <span className="text-slate-600">{b.date}</span>
      </nav>

      <h1 className="text-xl font-extrabold">📈 {formatDateKo(b.date)} 경제 브리핑</h1>
      <p className="mt-1 text-xs text-slate-400">
        생성 {b.created_at.slice(0, 16).replace("T", " ")}
        {b.model && ` · ${b.model}`}
      </p>

      <div
        className="mt-6 rounded-2xl border border-slate-100 bg-white p-5 text-[15px] leading-relaxed shadow-sm [&_strong]:mt-3 [&_strong]:block [&_strong]:text-slate-900"
        dangerouslySetInnerHTML={{ __html: mdToHtml(b.body_md) }}
      />

      {indicators.length > 0 && (
        <section className="mt-8">
          <h2 className="text-sm font-bold text-slate-400">이날의 핵심 지표</h2>
          <div className="mt-2 overflow-x-auto rounded-2xl border border-slate-100 bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs text-slate-400">
                  <th className="px-4 py-2.5 font-medium">지표</th>
                  <th className="px-4 py-2.5 text-right font-medium">값</th>
                  <th className="px-4 py-2.5 text-right font-medium">직전 대비</th>
                  <th className="px-4 py-2.5 text-right font-medium">기준시점</th>
                </tr>
              </thead>
              <tbody>
                {indicators.map(([name, v]) => (
                  <tr key={name} className="border-b border-slate-50 last:border-0">
                    <td className="px-4 py-2.5 font-medium">{name}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      {fmtNum(v.value)}
                      <span className="ml-0.5 text-xs text-slate-400">{v.unit}</span>
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      <DeltaBadge delta={v.delta} pct={v.pct} />
                    </td>
                    <td className="px-4 py-2.5 text-right text-xs text-slate-400">
                      {formatTs(v.ts)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <nav className="mt-8 flex justify-between text-sm">
        {older ? (
          <Link href={`/b/${older.date}`} className="text-blue-600 hover:underline">
            ← {older.date}
          </Link>
        ) : (
          <span />
        )}
        {newer ? (
          <Link href={`/b/${newer.date}`} className="text-blue-600 hover:underline">
            {newer.date} →
          </Link>
        ) : (
          <span />
        )}
      </nav>
    </main>
  );
}
