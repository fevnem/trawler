"use client";

import { ArrowDown } from "@phosphor-icons/react";
import { useMemo, useState } from "react";
import { duration } from "@/lib/api";

type Props = {
  token: string;
  mode: "gif" | "clip";
  duration: number | null;
};

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function TimePanel({ token, mode, duration: total }: Props) {
  const max = Math.max(Math.floor(total ?? 60), 2);
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(Math.min(max, mode === "gif" ? 5 : 30));
  const [width, setWidth] = useState(480);
  const [fps, setFps] = useState(12);

  const href = useMemo(() => {
    const from = clamp(start, 0, Math.max(end - 0.2, 0));
    const to = clamp(end, from + 0.2, max);
    if (mode === "gif") {
      return `/api/gif/${token}?start=${from}&end=${to}&width=${width}&fps=${fps}`;
    }
    return `/api/dl/${token}?start=${from}&end=${to}`;
  }, [token, mode, start, end, width, fps, max]);

  const span = Math.max(end - start, 0);

  return (
    <div className="border-t border-rule pt-5">
      <div className="flex flex-wrap items-end gap-x-8 gap-y-6">
        <div>
          <p className="mb-2 text-xs text-muted">Range in seconds</p>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={0}
              max={max}
              step={0.5}
              value={start}
              onChange={(event) => setStart(Number(event.target.value))}
              aria-label="Start time in seconds"
              className="num w-24 border border-rule bg-card px-3 py-2 text-sm"
            />
            <span className="text-xs text-muted">to</span>
            <input
              type="number"
              min={0}
              max={max}
              step={0.5}
              value={end}
              onChange={(event) => setEnd(Number(event.target.value))}
              aria-label="End time in seconds"
              className="num w-24 border border-rule bg-card px-3 py-2 text-sm"
            />
          </div>
        </div>

        {mode === "gif" ? (
          <>
            <div>
              <p className="mb-2 text-xs text-muted">Width</p>
              <select
                value={width}
                onChange={(event) => setWidth(Number(event.target.value))}
                aria-label="GIF width"
                className="num h-[38px] w-24 border border-rule bg-card px-2 text-sm"
              >
                {[320, 480, 640].map((value) => (
                  <option key={value} value={value}>
                    {value}px
                  </option>
                ))}
              </select>
            </div>
            <div>
              <p className="mb-2 text-xs text-muted">Frame rate</p>
              <select
                value={fps}
                onChange={(event) => setFps(Number(event.target.value))}
                aria-label="Frames per second"
                className="num h-[38px] w-24 border border-rule bg-card px-2 text-sm"
              >
                {[10, 12, 15, 20].map((value) => (
                  <option key={value} value={value}>
                    {value} fps
                  </option>
                ))}
              </select>
            </div>
          </>
        ) : null}

        <p className="num ml-auto pb-3 text-xs text-muted">
          {duration(span)} selected
          {mode === "gif" ? " / max 30s" : ""} / source {duration(total)}
        </p>

        <a href={href} className="btn">
          {mode === "gif" ? "Make GIF" : "Download clip"}
          <ArrowDown size={15} weight="bold" />
        </a>
      </div>
    </div>
  );
}
