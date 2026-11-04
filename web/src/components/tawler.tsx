"use client";

import Link from "next/link";
import { useState } from "react";
import { duration, probe, type Playlist, type Probe, type Site } from "@/lib/api";
import { Omni } from "./omni";
import { Result } from "./result";

const SAMPLES = [
  { label: "a track", url: "https://soundcloud.com/forss/flickermood" },
  { label: "a film", url: "https://archive.org/details/BigBuckBunny_124" },
  { label: "a direct file", url: "https://www.w3schools.com/html/mov_bbb.mp4" },
];

export function Tawler({ total, board }: { total: number; board: Site[] }) {
  const [url, setUrl] = useState("");
  const [data, setData] = useState<Probe | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(value?: string) {
    const target = (value ?? url).trim();
    if (target.length < 8) return;
    setUrl(target);
    setBusy(true);
    setError(null);
    try {
      setData(await probe(target));
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Could not read that link.");
    } finally {
      setBusy(false);
    }
  }

  const filled = Boolean(data);

  return (
    <div className="flex flex-1 flex-col">
      <section className={filled ? "pt-8" : "flex flex-1 flex-col justify-center pb-10"}>
        <div
          className={
            filled ? "" : "flex w-full flex-col gap-12 lg:flex-row lg:items-end lg:justify-between lg:gap-20"
          }
        >
        <div className={filled ? "" : "w-full max-w-[820px]"}>
        {!filled ? (
          <>
            <h1 className="display max-w-[24ch] text-[clamp(1.9rem,3.6vw,2.85rem)]">
              Paste a link.
              <br />
              Take the file.
            </h1>
            <p className="mt-4 max-w-[46ch] text-[15px] leading-relaxed text-muted">
              {total > 0 ? (
                <>
                  Video, audio, GIF or a trimmed clip, pulled from{" "}
                  <span className="num text-ink">{total.toLocaleString("en-US")}</span> sites. Nothing
                  is kept on the server.
                </>
              ) : (
                <>Video, audio, GIF or a trimmed clip from every site the reader knows. Nothing is kept on the server.</>
              )}
            </p>
          </>
        ) : null}

        <div className={filled ? "" : "mt-8"}>
          <Omni
            value={url}
            onChange={setUrl}
            onSubmit={() => run()}
            busy={busy}
            compact={filled}
          />
        </div>

        {!filled ? (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-muted">Try</span>
            {SAMPLES.map((sample) => (
              <button
                key={sample.url}
                type="button"
                onClick={() => run(sample.url)}
                className="num border border-rule px-2.5 py-1 text-[11px] text-muted transition-colors hover:border-ink hover:text-ink"
              >
                {sample.label}
              </button>
            ))}
          </div>
        ) : null}

        {error ? (
          <p role="alert" className="mt-3 border-l-2 border-signal pl-3 text-sm">
            {error}
          </p>
        ) : null}
        </div>

        {!filled && board.length ? <Board sites={board} total={total} /> : null}
        </div>
      </section>

      <div className={`h-px w-full overflow-hidden bg-rule ${busy ? "" : "opacity-0"}`}>
        <div className="progress-bar h-px w-1/3 bg-signal" />
      </div>

      {data?.kind === "media" ? <Result media={data} /> : null}
      {data?.kind === "playlist" ? <PlaylistView data={data} onPick={run} /> : null}
    </div>
  );
}

function Board({ sites, total }: { sites: Site[]; total: number }) {
  return (
    <div className="hidden w-[260px] shrink-0 lg:block">
      <div className="border-t border-rule pt-2">
        {sites.map((site) => (
          <div key={site.name} className="flex items-baseline justify-between gap-3 py-1.5">
            <span className="num text-[11px] lowercase text-muted">{site.name}</span>
          </div>
        ))}
        <Link
          href="/sites"
          className="num mt-2 block border-t border-rule pt-2 text-[11px] text-signal"
        >
          +{Math.max(total - sites.length, 0).toLocaleString("en-US")} more
        </Link>
      </div>
    </div>
  );
}

function PlaylistView({ data, onPick }: { data: Playlist; onPick: (url: string) => void }) {
  return (
    <div className="pb-24 pt-8">
      <p className="text-xs text-muted">{data.site.name}</p>
      <h2 className="display mt-2 text-3xl">{data.title}</h2>
      <p className="num mt-2 text-sm text-muted">{data.count} items</p>

      <div className="mt-8 border-t border-rule">
        {data.entries.map((entry, index) => (
          <button
            key={`${entry.id}-${index}`}
            type="button"
            onClick={() => onPick(entry.url)}
            className="flex w-full items-center gap-4 border-b border-rule py-3 text-left transition-colors hover:bg-[#efeee7]"
          >
            <span className="num w-8 shrink-0 text-xs text-muted">{String(index + 1).padStart(2, "0")}</span>
            <span className="flex-1 truncate text-sm">{entry.title}</span>
            <span className="num shrink-0 text-xs text-muted">{duration(entry.duration)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
