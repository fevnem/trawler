"""Turn a raw yt-dlp info dict into the shape the API and the UI expect.

Separated from the probe call so the rules about formats, containers and preview
selection live in one readable place.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from ..config import settings
from . import tickets

_SAFE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_KEEP_HEADERS = {"User-Agent", "Referer", "Cookie", "Accept-Language", "Origin"}
VIDEO_EXT = {"mp4", "mkv", "webm", "mov", "flv", "avi", "m4v", "ts", "3gp", "ogv"}
AUDIO_EXT = {"m4a", "mp3", "opus", "ogg", "oga", "wav", "flac", "aac", "weba"}


class ProbeError(Exception):
    pass


def headers_of(info: dict) -> dict:
    raw = info.get("http_headers") or {}
    out = {k: v for k, v in raw.items() if k in _KEEP_HEADERS and v}
    out.setdefault("User-Agent", settings.user_agent)
    return out


def _name(title: str, ext: str) -> str:
    clean = _SAFE.sub(" ", title or "download").strip()
    clean = re.sub(r"\s+", " ", clean)[:110]
    return f"{clean}.{ext}"


def _size(fmt: dict) -> int | None:
    return fmt.get("filesize") or fmt.get("filesize_approx")


def _best_audio(formats: list[dict], prefer_aac: bool) -> dict | None:
    pool = [f for f in formats if f.get("acodec") not in (None, "none") and f.get("vcodec") == "none"]
    if not pool:
        return None
    if prefer_aac:
        aac = [f for f in pool if str(f.get("acodec", "")).startswith("mp4a")]
        if aac:
            pool = aac
    return max(pool, key=lambda f: (f.get("abr") or 0, f.get("tbr") or 0))


def _kinds(fmt: dict) -> tuple[bool, bool]:
    """Codecs can be null on generic files, so fall back to the container."""
    vcodec, acodec = fmt.get("vcodec"), fmt.get("acodec")
    ext = (fmt.get("ext") or "").lower()
    if vcodec in (None, "none") and acodec in (None, "none"):
        if ext in AUDIO_EXT:
            return False, True
        if ext in VIDEO_EXT:
            return True, True
        return False, False
    return vcodec not in (None, "none"), acodec not in (None, "none")


def _container(vcodec: str) -> str:
    v = (vcodec or "").lower()
    if v.startswith(("vp9", "vp09", "av01", "opus")):
        return "webm"
    return "mp4"


def _playlist(info: dict) -> dict:
    entries = []
    for entry in (info.get("entries") or [])[:60]:
        if not entry:
            continue
        entries.append(
            {
                "title": entry.get("title"),
                "url": entry.get("url") or entry.get("webpage_url"),
                "duration": entry.get("duration"),
                "id": entry.get("id"),
            }
        )
    if not entries:
        raise ProbeError("This playlist is empty or private.")
    return {
        "kind": "playlist",
        "title": info.get("title") or "Playlist",
        "site": {"name": info.get("extractor_key") or "Unknown", "domain": None},
        "count": len(entries),
        "entries": entries,
    }


def normalize(info: dict, url: str) -> dict:
    if info.get("_type") in ("playlist", "multi_video"):
        return _playlist(info)

    formats = [f for f in (info.get("formats") or []) if f.get("url") and f.get("ext") != "mhtml"]
    if not formats:
        raise ProbeError("No downloadable formats were found for this link.")

    headers = headers_of(info)
    title = info.get("title") or "download"
    video, audio = [], []

    for fmt in formats:
        has_video, has_audio = _kinds(fmt)
        if not has_video and not has_audio:
            continue
        vcodec = fmt.get("vcodec") if has_video else None
        acodec = fmt.get("acodec") if has_audio else None
        entry = {
            "id": fmt.get("format_id"),
            "ext": fmt.get("ext"),
            "height": fmt.get("height"),
            "width": fmt.get("width"),
            "fps": fmt.get("fps"),
            "vcodec": None if vcodec in (None, "none") else vcodec,
            "acodec": None if acodec in (None, "none") else acodec,
            "size": _size(fmt),
            "note": fmt.get("format_note"),
            "hdr": fmt.get("dynamic_range"),
            "proto": fmt.get("protocol"),
        }

        if has_video:
            container = _container(vcodec or "")
            mate = _best_audio(formats, prefer_aac=container == "mp4")
            payload = {
                "k": "v",
                "u": fmt["url"],
                "h": headers,
                "n": _name(title, container),
                "x": container,
                "vc": vcodec,
                "p": fmt.get("protocol"),
            }
            if not has_audio:
                if not mate:
                    continue
                payload["a"] = mate["url"]
                payload["ah"] = headers
                payload["ac"] = mate.get("acodec")
            else:
                payload["k"] = "m"
            entry["token"] = tickets.sign(payload)
            entry["muxed"] = payload["k"] == "m"
            video.append(entry)
        else:
            entry["abr"] = fmt.get("abr") or fmt.get("tbr")
            entry["token"] = tickets.sign(
                {
                    "k": "a",
                    "u": fmt["url"],
                    "h": headers,
                    "n": _name(title, fmt.get("ext") or "m4a"),
                    "x": fmt.get("ext") or "m4a",
                    "ac": acodec,
                    "p": fmt.get("protocol"),
                }
            )
            audio.append(entry)

    video.sort(key=lambda f: (f["height"] or 0, f["fps"] or 0, f["size"] or 0), reverse=True)
    audio.sort(key=lambda f: f.get("abr") or 0, reverse=True)

    return {
        "kind": "media",
        "title": info.get("title"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader") or info.get("channel"),
        "webpage_url": info.get("webpage_url") or url,
        "is_live": bool(info.get("is_live")),
        "site": {
            "name": info.get("extractor_key") or "Unknown",
            "domain": (urlparse(info.get("webpage_url") or url).hostname or "").removeprefix("www.") or None,
        },
        "thumbnail": _thumbnail(info, headers),
        "preview": _preview(video, audio),
        "video": video,
        "audio": audio,
        "subtitles": _subtitles(info, headers),
    }


def _thumbnail(info: dict, headers: dict) -> str | None:
    thumb = info.get("thumbnail")
    return tickets.sign({"k": "t", "u": thumb, "h": headers}) if thumb else None


def _preview(video: list[dict], audio: list[dict]) -> dict | None:
    muxed = [f for f in video if f["muxed"]]
    progressive = [f for f in (muxed or video) if f.get("proto") in ("http", "https")]
    if progressive:
        pick = next((f for f in progressive if f["ext"] in ("mp4", "webm")), progressive[0])
        return {"token": pick["token"], "ext": pick["ext"], "muxed": pick["muxed"], "video": True}
    sound = [f for f in audio if f.get("proto") in ("http", "https")]
    if sound:
        return {"token": sound[0]["token"], "ext": sound[0]["ext"], "muxed": False, "video": False}
    return None


def _subtitles(info: dict, headers: dict) -> list[dict]:
    subs: list[dict] = []
    for lang, tracks in (info.get("subtitles") or {}).items():
        for track in tracks:
            if track.get("ext") in ("vtt", "srt", "ttml", "json3"):
                subs.append(
                    {
                        "lang": lang,
                        "name": track.get("name") or lang,
                        "ext": track.get("ext"),
                        "auto": False,
                        "token": tickets.sign({"k": "s", "u": track["url"], "h": headers, "x": track["ext"]}),
                    }
                )
                break
    for lang, tracks in (info.get("automatic_captions") or {}).items():
        if any(s["lang"] == lang for s in subs):
            continue
        for track in tracks:
            if track.get("ext") == "vtt":
                subs.append(
                    {
                        "lang": lang,
                        "name": track.get("name") or lang,
                        "ext": "vtt",
                        "auto": True,
                        "token": tickets.sign({"k": "s", "u": track["url"], "h": headers, "x": "vtt"}),
                    }
                )
                break
    return subs
