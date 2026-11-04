"""Extractor inventory, built once at import from the installed yt-dlp."""

from __future__ import annotations

import re
from functools import lru_cache

from yt_dlp.extractor import gen_extractor_classes

_DOMAIN = re.compile(r"\b((?:[a-z0-9][a-z0-9-]*\.)+[a-z]{2,24})\b", re.I)
_SKIP = {"generic", "html5", "anvato", "common", "commonprotocols"}


def _patterns(cls) -> list[str]:
    raw = getattr(cls, "_VALID_URL", "")
    if isinstance(raw, (list, tuple)):
        return [p for p in raw if isinstance(p, str)]
    return [raw] if isinstance(raw, str) else []


def _domain_of(cls) -> str | None:
    name = (getattr(cls, "IE_NAME", "") or "").split(":")[0].lower().replace("-", "")
    if not name:
        return None
    for raw in _patterns(cls):
        found = _DOMAIN.findall(raw.replace("\\", ""))
        for host in found:
            host = host.lower()
            if host.startswith("www."):
                host = host[4:]
            if "." not in host or host.endswith(".onion"):
                continue
            first = host.split(".")[0].replace("-", "")
            if name in host.replace("-", "") or first in name or name[:5] == first[:5]:
                return host
    return None


@lru_cache(maxsize=1)
def catalog() -> list[dict]:
    seen: set[str] = set()
    items: list[dict] = []
    for cls in gen_extractor_classes():
        name = getattr(cls, "IE_NAME", None)
        if not name or not isinstance(name, str):
            continue
        if name.lower() in _SKIP or name.lower() in seen:
            continue
        seen.add(name.lower())
        items.append({"name": name, "domain": _domain_of(cls)})
    items.sort(key=lambda item: item["name"].lower())
    return items


@lru_cache(maxsize=1)
def matcher() -> list[tuple[re.Pattern, str]]:
    """Compiled URL patterns so the frontend can name a site before probing."""
    out: list[tuple[re.Pattern, str]] = []
    for cls in gen_extractor_classes():
        name = getattr(cls, "IE_NAME", None)
        if not name or not isinstance(name, str):
            continue
        for raw in _patterns(cls):
            try:
                out.append((re.compile(raw), name))
            except re.error:
                continue
    return out


def match(url: str) -> str | None:
    for pattern, name in matcher():
        try:
            if pattern.match(url):
                return name
        except Exception:  # noqa: BLE001
            continue
    return None
