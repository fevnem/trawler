import Link from "next/link";
import { SiteIndex } from "@/components/site-index";
import type { Site } from "@/lib/api";

const ORIGIN = process.env.API_ORIGIN ?? "http://127.0.0.1:8010";

async function loadSites(): Promise<Site[]> {
  try {
    const response = await fetch(`${ORIGIN}/api/sites`, { next: { revalidate: 3600 } });
    if (!response.ok) return [];
    const payload = (await response.json()) as { sites?: Site[] };
    return payload.sites ?? [];
  } catch {
    return [];
  }
}

export default async function SitesPage() {
  const sites = await loadSites();

  return (
    <main className="mx-auto w-full max-w-[1400px] px-5 sm:px-8">
      <header className="flex h-16 items-center justify-between border-b border-rule">
        <Link href="/" className="wordmark text-xl">
          trawler
        </Link>
        <Link href="/" className="text-sm text-muted transition-colors hover:text-ink">
          Back to the field
        </Link>
      </header>

      <h1 className="display mt-12 max-w-[18ch] text-[clamp(2rem,4vw,3.2rem)]">
        Everything the reader knows.
      </h1>
      <p className="mt-4 max-w-[56ch] text-sm leading-relaxed text-muted">
        The list comes from the extractors compiled into the running build. If a site is missing,
        a direct media link may still resolve through the generic reader.
      </p>

      <SiteIndex sites={sites} />
    </main>
  );
}
