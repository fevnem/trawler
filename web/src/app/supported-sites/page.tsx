import { SiteIndex } from "@/components/site-index";
import type { Site } from "@/lib/api";

const ORIGIN = process.env.API_ORIGIN ?? "http://127.0.0.1:8010";

export const dynamic = "force-dynamic";

async function loadSites(): Promise<Site[]> {
  try {
    const response = await fetch(`${ORIGIN}/api/sites`, { cache: "no-store" });
    if (!response.ok) return [];
    const payload = (await response.json()) as { sites?: Site[] };
    return payload.sites ?? [];
  } catch {
    return [];
  }
}

export default async function SupportedSitesPage() {
  const sites = await loadSites();

  return (
    <div>
      <h1 className="display mt-12 max-w-[18ch] text-[clamp(2rem,4vw,3.2rem)]">
        Everything the reader knows.
      </h1>
      <p className="mt-4 max-w-[56ch] text-sm leading-relaxed text-muted">
        The list comes from the extractors compiled into the running build. If a site is missing,
        a direct media link may still resolve through the generic reader.
      </p>

      <SiteIndex sites={sites} />
    </div>
  );
}
