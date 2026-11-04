export type Site = { name: string; domain: string | null };

export type Fmt = {
  id: string;
  ext: string;
  height: number | null;
  width: number | null;
  fps: number | null;
  vcodec: string | null;
  acodec: string | null;
  size: number | null;
  note: string | null;
  hdr: string | null;
  abr?: number | null;
  muxed: boolean;
  token: string;
};

export type Sub = { lang: string; name: string; ext: string; auto: boolean; token: string };

export type Media = {
  kind: "media";
  title: string;
  duration: number | null;
  uploader: string | null;
  webpage_url: string;
  is_live: boolean;
  site: Site;
  thumbnail: string | null;
  preview: { token: string; ext: string; muxed: boolean; video?: boolean } | null;
  video: Fmt[];
  audio: Fmt[];
  subtitles: Sub[];
  elapsed_ms: number;
  matched: string | null;
};

export type Playlist = {
  kind: "playlist";
  title: string;
  site: Site;
  count: number;
  entries: { title: string; url: string; duration: number | null; id: string }[];
};

export type Probe = Media | Playlist;

export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function apiPath(path: string): string {
  return `${BASE_PATH}${path}`;
}

export async function probe(url: string): Promise<Probe> {
  const response = await fetch(apiPath("/api/probe"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ url }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.detail ?? "Could not read that link.");
  }
  return payload as Probe;
}

export async function matchSite(url: string): Promise<string | null> {
  if (!/^https?:\/\/.+\..+/.test(url)) return null;
  try {
    const response = await fetch(apiPath(`/api/match?url=${encodeURIComponent(url)}`));
    if (!response.ok) return null;
    const payload = (await response.json()) as { name: string | null };
    return payload.name;
  } catch {
    return null;
  }
}

export function bytes(size: number | null | undefined): string {
  if (!size || size <= 0) return "size n/a";
  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value >= 10 ? Math.round(value) : value.toFixed(1)} ${units[unit]}`;
}

export function duration(seconds: number | null | undefined): string {
  if (!seconds || seconds < 0) return "--:--";
  const total = Math.round(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

export function quality(format: Fmt): string {
  if (!format.height) return format.abr ? `${Math.round(format.abr)} kbps` : "auto";
  const base = `${format.height}p`;
  return format.fps && format.fps > 30 ? `${base}${Math.round(format.fps)}` : base;
}

export function codec(format: Fmt): string {
  const parts = [format.vcodec, format.acodec].filter(Boolean) as string[];
  return parts.length ? parts.join(" + ") : "—";
}
