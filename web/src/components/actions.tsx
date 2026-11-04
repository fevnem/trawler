"use client";

import { ArrowDown, FileText, FilmStrip, ImageSquare, MusicNotes, Scissors } from "@phosphor-icons/react";
import { useState } from "react";
import { apiPath, bytes, type Media } from "@/lib/api";
import { FormatTable } from "./format-table";
import { TimePanel } from "./time-panel";

type Tab = "video" | "audio" | "gif" | "clip" | "subs" | "thumb";

const AUDIO_TARGETS = ["mp3", "m4a", "opus", "wav", "flac"];

export function Actions({ media }: { media: Media }) {
  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [];
  if (media.video.length) tabs.push({ id: "video", label: "Video", icon: <FilmStrip size={15} /> });
  if (media.audio.length) tabs.push({ id: "audio", label: "Audio", icon: <MusicNotes size={15} /> });
  if (media.preview?.video && media.video.length) tabs.push({ id: "gif", label: "GIF", icon: <ImageSquare size={15} /> });
  if (media.video.length) tabs.push({ id: "clip", label: "Clip", icon: <Scissors size={15} /> });
  if (media.subtitles.length) tabs.push({ id: "subs", label: "Subtitles", icon: <FileText size={15} /> });
  if (media.thumbnail) tabs.push({ id: "thumb", label: "Cover", icon: <ImageSquare size={15} /> });

  const [tab, setTab] = useState<Tab>(tabs[0]?.id ?? "video");
  const [target, setTarget] = useState("mp3");
  const source = media.preview ?? (media.video[0] ? { token: media.video[0].token } : null);
  const bestAudio = media.audio[0];

  return (
    <div>
      <div className="flex flex-wrap items-center gap-6 border-b border-rule">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            data-active={tab === item.id}
            onClick={() => setTab(item.id)}
            className="tab inline-flex items-center gap-1.5"
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </div>

      <div className="pt-5">
        {tab === "video" ? <FormatTable formats={media.video} empty="No video streams." /> : null}

        {tab === "audio" ? (
          <div>
            <div className="flex flex-wrap items-end gap-4 border-b border-rule pb-5">
              <div>
                <p className="mb-2 text-xs text-muted">Convert to</p>
                <div className="flex flex-wrap gap-2">
                  {AUDIO_TARGETS.map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setTarget(option)}
                      className={`num border px-3 py-1.5 text-xs transition-colors ${
                        target === option
                          ? "border-signal bg-signal text-paper"
                          : "border-rule text-muted hover:border-ink hover:text-ink"
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
              {bestAudio ? (
                <a href={apiPath(`/api/dl/${bestAudio.token}?to=${target}`)} className="btn-quiet ml-auto">
                  Convert and save
                </a>
              ) : null}
            </div>
            <p className="mb-2 mt-5 text-xs text-muted">Source streams</p>
            <FormatTable formats={media.audio} empty="No audio-only streams. Use the video tab." />
          </div>
        ) : null}

        {tab === "gif" && source ? (
          <TimePanel token={source.token} mode="gif" duration={media.duration} />
        ) : null}

        {tab === "clip" && source ? (
          <TimePanel token={source.token} mode="clip" duration={media.duration} />
        ) : null}

        {tab === "subs" ? (
          <div className="border-t border-rule">
            {media.subtitles.map((sub) => (
              <div
                key={`${sub.lang}-${sub.ext}`}
                className="flex items-center justify-between gap-4 border-b border-rule py-3"
              >
                <div className="flex items-baseline gap-3">
                  <span className="num text-sm">{sub.lang}</span>
                  <span className="text-xs text-muted">{sub.name}</span>
                  {sub.auto ? <span className="num text-[11px] text-muted">auto</span> : null}
                </div>
                <a href={apiPath(`/api/sub/${sub.token}`)} className="row-link text-sm">
                  {sub.ext}
                </a>
              </div>
            ))}
          </div>
        ) : null}

        {tab === "thumb" && media.thumbnail ? (
          <div className="flex flex-wrap items-start gap-6 border-t border-rule pt-5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={apiPath(`/api/thumb/${media.thumbnail}`)}
              alt="Cover art"
              className="max-h-64 border border-rule object-contain"
            />
            <a href={apiPath(`/api/thumb/${media.thumbnail}`)} download className="btn">
              Save cover
              <ArrowDown size={15} weight="bold" />
            </a>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function bestFormat(media: Media) {
  const pick = media.video[0] ?? media.audio[0];
  if (!pick) return null;
  const label = pick.height ? `${pick.height}p ${pick.ext.toUpperCase()}` : pick.ext.toUpperCase();
  return { token: pick.token, label, size: bytes(pick.size) };
}
