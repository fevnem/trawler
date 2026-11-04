"use client";

import { LinkSimple } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import { matchSite } from "@/lib/api";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  busy: boolean;
  compact: boolean;
};

export function Omni({ value, onChange, onSubmit, busy, compact }: Props) {
  const [site, setSite] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!value) {
      setSite(null);
      setChecked(false);
      return;
    }
    const id = setTimeout(async () => {
      setSite(await matchSite(value));
      setChecked(true);
    }, 260);
    return () => clearTimeout(id);
  }, [value]);

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (value.trim().length < 8) {
          input.current?.focus();
          return;
        }
        onSubmit();
      }}
      className={`flex items-stretch border border-line bg-card transition-colors duration-200 focus-within:border-signal ${
        compact ? "h-14" : "h-[4.5rem]"
      }`}
    >
      <div className="flex min-w-0 flex-1 items-center gap-3 px-4">
        <LinkSimple size={compact ? 17 : 20} weight="bold" className="shrink-0 text-muted" />
        <input
          ref={input}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="https://"
          spellCheck={false}
          autoComplete="off"
          inputMode="url"
          aria-label="Link to download"
          className={`field ${compact ? "text-base" : ""}`}
        />
        {checked && value ? (
          <span className="num hidden shrink-0 text-xs text-muted sm:block">
            {site ?? "not in the list"}
          </span>
        ) : null}
      </div>

      <button
        type="submit"
        className={`btn shrink-0 border-l border-line ${compact ? "w-24 text-sm" : "w-[7.5rem]"}`}
      >
        {busy ? "Reading" : "Fetch"}
      </button>
    </form>
  );
}
