import Link from "next/link";
import { formatDateKo, loadBriefings, snippet } from "@/lib/briefings";

export const dynamic = "force-static";

export default function HomePage() {
  const { briefings, updated_at } = loadBriefings();
  const latest = briefings[0];

  return (
    <main className="mx-auto max-w-xl px-4 py-8">
      <h1 className="text-2xl font-extrabold">📈 오늘의 경제, 내 말로</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-500">
        기준금리·환율·물가가 <b className="text-slate-700">내 대출이자와 생활비</b>에 무슨
        뜻인지, 매일 아침 쉬운 말로 풀어드립니다.
      </p>
      {updated_at && (
        <p className="mt-1 text-xs text-slate-400">
          마지막 갱신 {updated_at.slice(0, 16).replace("T", " ")}
        </p>
      )}

      {latest && (
        <Link
          href={`/b/${latest.date}`}
          className="mt-6 block rounded-2xl border border-blue-100 bg-white p-5 shadow-sm transition hover:shadow"
        >
          <div className="text-xs font-semibold text-blue-600">오늘의 브리핑</div>
          <div className="mt-1 font-bold">{formatDateKo(latest.date)}</div>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            {snippet(latest.body_md, 140)}
          </p>
        </Link>
      )}

      <h2 className="mt-10 text-sm font-bold text-slate-400">지난 브리핑</h2>
      <ul className="mt-2 divide-y divide-slate-100">
        {briefings.slice(1).map((b) => (
          <li key={b.date}>
            <Link href={`/b/${b.date}`} className="block py-4 transition hover:bg-white">
              <div className="text-sm font-semibold">{formatDateKo(b.date)}</div>
              <p className="mt-1 text-sm text-slate-500">{snippet(b.body_md)}</p>
            </Link>
          </li>
        ))}
      </ul>
      {briefings.length === 0 && (
        <p className="mt-6 text-sm text-slate-400">아직 브리핑이 없습니다.</p>
      )}
    </main>
  );
}
