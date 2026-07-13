import { SITE_URL, formatDateKo, loadBriefings, snippet } from "@/lib/briefings";

export const dynamic = "force-static";

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** created_at(ISO) 우선, 실패 시 date 기준 07:00 KST(발행 시각)로 RFC-822 변환 */
function rfc822(createdAt: string, date: string): string {
  const t = new Date(createdAt);
  if (!Number.isNaN(t.getTime())) return t.toUTCString();
  return new Date(`${date}T07:00:00+09:00`).toUTCString();
}

export async function GET() {
  const data = loadBriefings();
  // 최신순 50건 — 검색엔진·리더가 "새 글"로 인식하는 영역
  const items = [...data.briefings]
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 50);

  const itemsXml = items
    .map((b) => {
      const title = `${formatDateKo(b.date)} 경제 브리핑 — 기준금리·환율·물가`;
      return [
        "<item>",
        `<title>${esc(title)}</title>`,
        `<link>${SITE_URL}/b/${b.date}</link>`,
        `<guid isPermaLink="true">${SITE_URL}/b/${b.date}</guid>`,
        `<description>${esc(snippet(b.body_md, 200))}</description>`,
        `<pubDate>${rfc822(b.created_at, b.date)}</pubDate>`,
        "</item>",
      ].join("");
    })
    .join("\n");

  const lastBuild = data.updated_at
    ? new Date(data.updated_at).toUTCString()
    : new Date().toUTCString();

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>오늘의 경제, 내 말로 — 매일 아침 경제 브리핑</title>
<link>${SITE_URL}</link>
<description>기준금리·환율·물가 같은 한·미 핵심 경제 지표를 내 지갑 기준으로 풀어주는 매일 브리핑 피드.</description>
<language>ko</language>
<lastBuildDate>${lastBuild}</lastBuildDate>
${itemsXml}
</channel>
</rss>`;

  return new Response(xml, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
}
