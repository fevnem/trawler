"use client";

import { ArrowDown, ArrowUpRight } from "@phosphor-icons/react";
import { apiPath, duration, type Media } from "@/lib/api";
import { Actions, bestFormat } from "./actions";
import { Preview } from "./preview";

export function Result({ media }: { media: Media }) {
  const best = bestFormat(media);

  return (
    <div className="grid gap-10 pb-24 pt-10 lg:grid-cols-[1.5fr_1fr] lg:gap-14">
      <div className="min-w-0">
        <Preview media={media} />

        <div className="mt-4 grid grid-cols-3 border-y border-rule">
          <Fact label="Duration" value={media.duration ? duration(media.duration) : "unknown"} />
          <Fact label="Formats" value={String(media.video.length + media.audio.length)} bordered />
          <Fact label="Subtitles" value={String(media.subtitles.length)} bordered />
        </div>

        <div className="mt-8">
          <Actions media={media} />
        </div>
      </div>

      <aside className="min-w-0 self-start lg:sticky lg:top-8">
        <p className="mb-3 text-xs text-muted">{media.site.domain ?? media.site.name}</p>

        <h2 className="display text-3xl leading-[1.05] sm:text-4xl">{media.title}</h2>

        {media.uploader ? (
          <p className="mt-3 text-sm text-muted">
            <span className="text-xs text-muted">Uploaded by </span>
            {media.uploader}
          </p>
        ) : null}

        {best ? (
          <a href={apiPath(`/api/dl/${best.token}`)} className="btn mt-8 w-full">
            Download {best.label}
            <ArrowDown size={16} weight="bold" />
          </a>
        ) : null}

        <p className="num mt-3 text-xs text-muted">{best?.size ?? "size n/a"}</p>

        <a
          href={media.webpage_url}
          target="_blank"
          rel="noreferrer noopener"
          className="row-link mt-6 inline-flex items-center gap-1 text-sm"
        >
          Open the source page
          <ArrowUpRight size={13} weight="bold" />
        </a>

        <p className="mt-8 border-t border-rule pt-4 text-xs leading-relaxed text-muted">
          Files stream straight from the source to your browser. Nothing is written to disk, nothing
          is kept after the request ends.
        </p>
      </aside>
    </div>
  );
}

function Fact({ label, value, bordered }: { label: string; value: string; bordered?: boolean }) {
  return (
    <div className={`px-4 py-3 ${bordered ? "border-l border-rule" : ""}`}>
      <p className="text-[11px] text-muted">{label}</p>
      <p className="num mt-1 truncate text-sm">{value}</p>
    </div>
  );
}
