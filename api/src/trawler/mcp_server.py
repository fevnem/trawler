"""MCP surface for trawler.

Mounted at /api/mcp, behind the same rewrite the web app already uses. Tools never
move bytes: they return signed, expiring URLs minted by the same ticket code the
web app uses, and the client fetches those over HTTP.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, Any

import anyio
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field

from .config import settings
from .core import catalog, limits, tickets, ytdlp
from .core.normalize import ProbeError

INSTRUCTIONS = (
    "trawler reads media links and returns signed download URLs. "
    "Call probe first to see the available formats, then fetch the download_url it returns. "
    "Nothing is stored server side; every URL expires."
)

server = MCPServer(name="trawler", instructions=INSTRUCTIONS)
_MANAGER = None


def _absolute(path: str) -> str:
    base = (settings.public_origin or "http://localhost:3000").rstrip("/")
    return f"{base}{path}"


def _summary(info: dict) -> dict[str, Any]:
    if info.get("kind") == "playlist":
        return {
            "kind": "playlist",
            "title": info.get("title"),
            "count": info.get("count"),
            "entries": info.get("entries", [])[:25],
        }

    formats = []
    for kind, pool in (("video", info.get("video", [])), ("audio", info.get("audio", []))):
        for fmt in pool:
            if fmt.get("height"):
                quality = f"{fmt['height']}p"
            elif fmt.get("abr"):
                quality = f"{round(fmt['abr'])} kbps"
            else:
                quality = kind
            formats.append(
                {
                    "id": fmt.get("id"),
                    "kind": kind,
                    "container": fmt.get("ext"),
                    "quality": quality,
                    "vcodec": fmt.get("vcodec"),
                    "acodec": fmt.get("acodec"),
                    "size_bytes": fmt.get("size"),
                    "download_url": _absolute(f"/api/dl/{fmt['token']}"),
                }
            )

    subtitles = [
        {"lang": sub["lang"], "ext": sub["ext"], "auto": sub["auto"], "url": _absolute(f"/api/sub/{sub['token']}")}
        for sub in info.get("subtitles", [])
    ]

    return {
        "kind": "media",
        "title": info.get("title"),
        "site": info.get("site", {}).get("name"),
        "domain": info.get("site", {}).get("domain"),
        "uploader": info.get("uploader"),
        "duration_seconds": info.get("duration"),
        "webpage_url": info.get("webpage_url"),
        "cover_url": _absolute(f"/api/thumb/{info['thumbnail']}") if info.get("thumbnail") else None,
        "formats": formats,
        "subtitles": subtitles,
    }


async def _probe(url: str) -> dict:
    async with limits.probes:
        try:
            return await anyio.to_thread.run_sync(ytdlp.probe, url.strip())
        except ProbeError as exc:
            raise ValueError(str(exc)) from exc


@server.tool()
async def probe(
    url: Annotated[str, Field(description="Media page URL to read.")],
) -> dict:
    """Read a link: title, site, duration, downloadable formats and subtitle tracks."""
    return _summary(await _probe(url))


@server.tool()
async def list_sites(
    query: Annotated[str | None, Field(description="Filter by name or domain. Omit for the full list.")] = None,
) -> dict:
    """List the extractors this build can read."""
    items = catalog.catalog()
    if query:
        needle = query.lower()
        items = [s for s in items if needle in s["name"].lower() or needle in (s["domain"] or "")]
    return {"count": len(items), "sites": items[:200]}


@server.tool()
async def match(
    url: Annotated[str, Field(description="URL to test against the extractor list.")],
) -> dict:
    """Report which extractor claims a URL, without downloading anything."""
    return {"extractor": catalog.match(url)}


@server.tool()
async def download_link(
    url: Annotated[str, Field(description="Media page URL.")],
    format_id: Annotated[str | None, Field(description="Format id from probe. Omit for the best video.")] = None,
    start: Annotated[float | None, Field(description="Trim start in seconds.", ge=0)] = None,
    end: Annotated[float | None, Field(description="Trim end in seconds.", ge=0)] = None,
) -> dict:
    """Mint a signed download URL for one format, optionally trimmed."""
    info = await _probe(url)
    if info.get("kind") != "media":
        raise ValueError("That link is a playlist. Probe its entries individually.")

    pool = info.get("video") or info.get("audio") or []
    if not pool:
        raise ValueError("No downloadable formats.")

    chosen = pool[0]
    if format_id:
        chosen = next((f for f in pool if str(f.get("id")) == str(format_id)), None)
        if chosen is None:
            raise ValueError(f"Format {format_id} is not in this item. Call probe to list ids.")

    query = ""
    if start is not None:
        query = f"?start={start}" + (f"&end={end}" if end is not None else "")

    return {
        "format_id": chosen.get("id"),
        "container": chosen.get("ext"),
        "url": _absolute(f"/api/dl/{chosen['token']}{query}"),
        "expires_in_seconds": settings.token_ttl,
    }


@server.tool()
async def audio_link(
    url: Annotated[str, Field(description="Media page URL.")],
    target: Annotated[str, Field(description="mp3, m4a, opus, wav or flac.")] = "mp3",
) -> dict:
    """Mint a signed URL for the best audio stream, converted to the requested container."""
    info = await _probe(url)
    audio = info.get("audio") or []
    if not audio:
        raise ValueError("No audio-only stream for this item. Use the video formats instead.")
    if target not in ("mp3", "m4a", "opus", "wav", "flac"):
        raise ValueError("target must be mp3, m4a, opus, wav or flac.")
    return {
        "target": target,
        "url": _absolute(f"/api/dl/{audio[0]['token']}?to={target}"),
        "expires_in_seconds": settings.token_ttl,
    }


@server.tool()
async def gif_link(
    url: Annotated[str, Field(description="Media page URL.")],
    start: Annotated[float, Field(description="Start in seconds.", ge=0)],
    end: Annotated[float, Field(description="End in seconds.", ge=0)],
    width: Annotated[int, Field(description="Pixel width, 120-960.", ge=120, le=960)] = 480,
    fps: Annotated[int, Field(description="Frames per second, 4-30.", ge=4, le=30)] = 12,
) -> dict:
    """Mint a signed URL for an animated GIF cut from a range. Maximum span is 30 seconds."""
    info = await _probe(url)
    preview = info.get("preview")
    if not preview:
        raise ValueError("This item has no video stream to cut a GIF from.")
    return {
        "url": _absolute(f"/api/gif/{preview['token']}?start={start}&end={end}&width={width}&fps={fps}"),
        "expires_in_seconds": settings.token_ttl,
    }


@server.tool()
async def subtitle_link(
    url: Annotated[str, Field(description="Media page URL.")],
    lang: Annotated[str | None, Field(description="Language code. Omit for the first available track.")] = None,
) -> dict:
    """Mint a signed URL for one subtitle track."""
    info = await _probe(url)
    subs = info.get("subtitles") or []
    if not subs:
        raise ValueError("No subtitle tracks for this item.")
    chosen = next((s for s in subs if s["lang"] == lang), None) if lang else subs[0]
    if chosen is None:
        raise ValueError(f"No track for {lang}. Available: {', '.join(s['lang'] for s in subs[:20])}")
    return {"lang": chosen["lang"], "ext": chosen["ext"], "url": _absolute(f"/api/sub/{chosen['token']}")}


class BearerGuard:
    """Rejects any request without the configured bearer token."""

    def __init__(self, app, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        if not self.token or headers.get("authorization") != f"Bearer {self.token}":
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
            return
        await self.app(scope, receive, send)


def build_app(path: str = "/mcp"):
    """Return the ASGI app to mount, or None when MCP is not configured."""
    global _MANAGER
    if not settings.mcp_token:
        return None
    app = server.streamable_http_app(
        streamable_http_path=path,
        json_response=True,
        stateless_http=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    # The session manager only exists once the transport app is built, and its
    # task group has to be started from the host app's lifespan.
    _MANAGER = server.session_manager
    return BearerGuard(app, settings.mcp_token)


@asynccontextmanager
async def mcp_lifespan():
    """Run the MCP session manager for the lifetime of the host app."""
    if _MANAGER is None:
        yield
        return
    async with _MANAGER.run():
        yield
