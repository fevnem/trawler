"use client";

import { ArrowDown } from "@phosphor-icons/react";
import { bytes, codec, quality, type Fmt } from "@/lib/api";

type Props = { formats: Fmt[]; empty: string };

export function FormatTable({ formats, empty }: Props) {
  if (!formats.length) {
    return <p className="border-t border-rule py-6 text-sm text-muted">{empty}</p>;
  }

  return (
    <div className="border-t border-rule">
      <div className="hidden grid-cols-[4.5rem_4.5rem_1fr_5.5rem_6rem] gap-4 border-b border-rule py-2 text-xs text-muted sm:grid">
        <span>Quality</span>
        <span>Container</span>
        <span>Codec</span>
        <span className="text-right">Size</span>
        <span className="text-right">Download</span>
      </div>

      {formats.map((format) => (
        <div
          key={format.id}
          className="group grid grid-cols-[1fr_auto] items-center gap-4 border-b border-rule py-3 transition-colors duration-150 hover:bg-hover sm:grid-cols-[4.5rem_4.5rem_1fr_5.5rem_6rem]"
        >
          <span className="num text-sm">{quality(format)}</span>

          <span className="num text-xs uppercase text-muted">{format.ext}</span>

          <span className="num col-span-2 truncate text-xs text-muted sm:col-span-1">
            {codec(format)}
            {format.hdr && format.hdr !== "SDR" ? ` / ${format.hdr}` : ""}
          </span>

          <span className="num hidden text-right text-xs text-muted sm:block">
            {format.size ? bytes(format.size) : "n/a"}
          </span>

          <a
            href={`/api/dl/${format.token}`}
            aria-label={`Download ${quality(format)} ${format.ext.toUpperCase()}`}
            className="row-link inline-flex items-center justify-end gap-1 justify-self-end text-sm"
          >
            Download
            <ArrowDown size={14} weight="bold" />
          </a>
        </div>
      ))}
    </div>
  );
}
