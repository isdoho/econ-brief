import fs from "fs";
import path from "path";

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://econ-brief.netlify.app";

export type IndicatorSnapshot = {
  value: number;
  delta: number | null;
  pct: number | null;
  ts: string;
  unit: string;
};

export type Briefing = {
  date: string; // YYYY-MM-DD
  model: string | null;
  created_at: string;
  body_md: string;
  payload: Record<string, IndicatorSnapshot> | null;
};

export type BriefingsDoc = {
  updated_at: string | null;
  briefings: Briefing[];
};

let cache: BriefingsDoc | null = null;

export function loadBriefings(): BriefingsDoc {
  if (cache) return cache;
  const file = path.join(process.cwd(), "public", "data", "briefings.json");
  cache = JSON.parse(fs.readFileSync(file, "utf-8")) as BriefingsDoc;
  return cache;
}

export function getBriefing(date: string): Briefing | undefined {
  return loadBriefings().briefings.find((b) => b.date === date);
}

/** body_md(굵게 ** + 줄바꿈만 사용)를 안전한 HTML로. */
export function mdToHtml(md: string): string {
  const escaped = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

/** 첫 문단 요약(목록·메타 설명용). 마크다운 기호 제거. */
export function snippet(md: string, n = 90): string {
  const plain = md.replace(/\*\*/g, "").replace(/\n+/g, " ").trim();
  return plain.length > n ? plain.slice(0, n) + "…" : plain;
}

/** 지표 관측시점 표기 정규화: 20260619→2026.06.19, 202605→2026.05, ISO→2026.06.17 */
export function formatTs(ts: string): string {
  if (ts.includes("-")) return ts.slice(0, 10).replaceAll("-", ".");
  if (ts.length === 8) return `${ts.slice(0, 4)}.${ts.slice(4, 6)}.${ts.slice(6)}`;
  if (ts.length === 6) return `${ts.slice(0, 4)}.${ts.slice(4)}`;
  return ts;
}

export function formatDateKo(date: string): string {
  const [y, m, d] = date.split("-").map(Number);
  const day = ["일", "월", "화", "수", "목", "금", "토"][new Date(y, m - 1, d).getDay()];
  return `${y}년 ${m}월 ${d}일 (${day})`;
}
