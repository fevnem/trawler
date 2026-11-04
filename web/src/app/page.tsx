import { Trawler } from "@/components/trawler";

const ORIGIN = process.env.API_ORIGIN ?? "http://127.0.0.1:8010";

export const dynamic = "force-dynamic";

async function siteCount(): Promise<number> {
  try {
    const response = await fetch(`${ORIGIN}/api/health`, { cache: "no-store" });
    if (!response.ok) return 0;
    const payload = (await response.json()) as { extractors?: number };
    return payload.extractors ?? 0;
  } catch {
    return 0;
  }
}

export default async function Page() {
  const total = await siteCount();
  return <Trawler total={total} />;
}
