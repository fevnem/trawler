"use client";

import { MusicNotes, PlayCircle } from "@phosphor-icons/react";
import { apiPath, type Media } from "@/lib/api";

export function Preview({ media }: { media: Media }) {
  const cover = media.thumbnail ? apiPath(`/api/thumb/${media.thumbnail}`) : null;

  if (!media.preview) {
    if (cover) {
      return (
        <div className="w-full border border-rule bg-card">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={cover} alt="" className="max-h-[420px] w-full object-contain" />
        </div>
      );
    }
    return (
      <div className="flex items-center gap-3 border border-rule bg-card px-4 py-6 text-sm text-muted">
        <PlayCircle size={20} />
        No inline preview for this source. The file is still downloadable below.
      </div>
    );
  }

  const src = apiPath(`/api/preview/${media.preview.token}`);
  const isVideo = media.preview.video !== false;

  if (isVideo) {
    return (
      <div className="relative w-full border border-rule bg-ink">
        <video
          key={src}
          src={src}
          poster={cover ?? undefined}
          controls
          autoPlay
          muted
          loop
          preload="metadata"
          playsInline
          className="aspect-video w-full"
        />
      </div>
    );
  }

  return (
    <div className="relative flex aspect-[16/9] w-full items-center justify-center overflow-hidden border border-rule bg-card">
      {cover ? (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={cover} alt="" className="absolute inset-0 h-full w-full object-cover opacity-25" />
          <div className="absolute inset-0 bg-paper/60" />
        </>
      ) : null}
      <div className="relative flex w-[80%] flex-col items-center gap-5">
        <MusicNotes size={28} className="text-muted" />
        <audio src={src} controls preload="metadata" className="w-full" />
      </div>
    </div>
  );
}
