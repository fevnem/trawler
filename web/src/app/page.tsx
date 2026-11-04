import Link from "next/link";
import { Trawler } from "@/components/trawler";
import type { Site } from "@/lib/api";

const ORIGIN = process.env.API_ORIGIN ?? "http://127.0.0.1:8010";
const FEATURED = ["youtube", "vimeo", "soundcloud", "bandcamp", "twitch", "tiktok", "dailymotion", "bilibili"];

async function load() {
  try {
    const [health, sites] = await Promise.all([
      fetch(`${ORIGIN}/api/health`, { next: { revalidate: 3600 } }),
      fetch(`${ORIGIN}/api/sites`, { next: { revalidate: 3600 } }),
    ]);
    const total = health.ok ? ((await health.json()) as { extractors?: number }).extractors ?? 0 : 0;
    const all = sites.ok ? ((await sites.json()) as { sites?: Site[] }).sites ?? [] : [];
    const picked = FEATURED.map((name) => all.find((site) => site.name.toLowerCase() === name)).filter(
      (site): site is Site => Boolean(site),
    );
    const board = picked.length >= 4 ? picked : all.slice(0, 8);
    return { total, board };
  } catch {
    return { total: 0, board: [] as Site[] };
  }
}

export default async function Page() {
  const { total, board } = await load();

  return (
    <main className="mx-auto flex min-h-[100dvh] w-full max-w-[1400px] flex-col px-5 sm:px-8">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-rule">
        <Link href="/" className="wordmark text-xl">
          trawler<span className="text-signal">.</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          <Link href="/sites" className="text-muted transition-colors hover:text-ink">
            Supported sites
          </Link>
        </nav>
      </header>

      <Trawler total={total} board={board} />

      <footer className="mt-auto flex flex-wrap items-baseline justify-between gap-4 border-t border-rule py-6">
        <p className="text-xs text-muted">Use it for content you have the right to keep.</p>
        <p className="num text-xs text-muted">
          trawler<span className="text-signal">.</span>
        </p>
      </footer>
    </main>
  );
}
