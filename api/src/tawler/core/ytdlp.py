"""The only module that calls yt_dlp.

A probe resolves metadata and mints a signed ticket per downloadable format, so
every later request is a pure pipe: no re-extraction, no cache, no storage.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

from ..config import settings
from . import catalog
from .normalize import ProbeError, normalize

__all__ = ["ProbeError", "probe"]


def probe(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ProbeError("That is not a valid link.")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noprogress": True,
        "socket_timeout": 20,
        "retries": 2,
        "cachedir": False,
        "extract_flat": "in_playlist",
        "http_headers": {"User-Agent": settings.user_agent},
    }
    if settings.cookies_file and Path(settings.cookies_file).is_file():
        opts["cookiefile"] = settings.cookies_file

    started = time.time()
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise ProbeError(_clean_error(str(exc))) from exc
    except Exception as exc:  # noqa: BLE001
        raise ProbeError("Could not read that link.") from exc

    if not info:
        raise ProbeError("Could not read that link.")

    result = normalize(info, url)
    result["elapsed_ms"] = int((time.time() - started) * 1000)
    result["matched"] = catalog.match(url)
    return result


def _clean_error(message: str) -> str:
    text = re.sub(r"\x1b\[[0-9;]*m", "", message.strip())
    text = re.sub(r"^ERROR:\s*", "", text)
    text = re.sub(r"^\[[^\]]+\]\s*[^:]*:\s*", "", text)
    lowered = text.lower()

    if "unsupported url" in lowered:
        return "That site is not in the extractor list."
    if "404" in lowered or "not found" in lowered:
        return "That link returned nothing. Check the address."
    if "403" in lowered or "forbidden" in lowered:
        return "The site refused the request. It may need cookies."
    if "private" in lowered:
        return "This item is private."
    if "sign in" in lowered or ("age" in lowered and "confirm" in lowered):
        return "This item needs an account to read."
    if "not available" in lowered or "geo" in lowered:
        return "This item is not available from here."
    if "timed out" in lowered or "timeout" in lowered:
        return "The site took too long to answer."
    if "unable to download webpage" in lowered:
        return "That page could not be read."
    if "is not a valid url" in lowered:
        return "That is not a valid link."

    first = text.split(". ")[0].strip()
    return (first or "Could not read that link.")[:160]
