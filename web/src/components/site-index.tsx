"use client";

import { useMemo, useState } from "react";
import type { Site } from "@/lib/api";

export function SiteIndex({ sites }: { sites: Site[] }) {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(150);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return sites;
    return sites.filter(
      (site) => site.name.toLowerCase().includes(needle) || (site.domain ?? "").includes(needle),
    );
  }, [sites, query]);

  const shown = filtered.slice(0, limit);

  return (
    <div className="pb-24">
      <div className="mt-10 flex items-center gap-3 border border-ink bg-card px-4">
        <input
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setLimit(150);
          }}
          placeholder="Filter by name or domain"
          aria-label="Filter supported sites"
          className="field h-14 text-lg"
        />
        <span className="num shrink-0 text-xs text-muted">
          {filtered.length.toLocaleString("en-US")} / {sites.length.toLocaleString("en-US")}
        </span>
      </div>

      <div className="mt-8 grid gap-x-10 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((site) => (
          <div
            key={site.name}
            className="flex items-baseline justify-between gap-4 border-b border-rule py-2.5"
          >
            <span className="truncate text-sm lowercase">{site.name}</span>
            <span className="num shrink-0 text-[11px] text-muted">{site.domain ?? ""}</span>
          </div>
        ))}
      </div>

      {filtered.length > shown.length ? (
        <button type="button" onClick={() => setLimit(limit + 300)} className="btn-quiet mt-8">
          Show more
        </button>
      ) : null}

      {!filtered.length ? (
        <p className="mt-10 border-t border-rule pt-6 text-sm text-muted">
          Nothing matches that name. A direct link to a media file still works through the generic
          reader.
        </p>
      ) : null}
    </div>
  );
}
