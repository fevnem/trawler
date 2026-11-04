import { Trawler } from "@/components/trawler";
import type { Site } from "@/lib/api";

const ORIGIN = process.env.API_ORIGIN ?? "http://127.0.0.1:8010";
const FEATURED = ["youtube", "vimeo", "soundcloud", "bandcamp", "twitch", "tiktok", "dailymotion", "bilibili"];

export const dynamic = "force-dynamic";

async function load() {
  try {
    const [health, sites] = await Promise.all([
      fetch(`${ORIGIN}/api/health`, { cache: "no-store" }),
      fetch(`${ORIGIN}/api/sites`, { cache: "no-store" }),
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
  return <Trawler total={total} board={board} />;
}
