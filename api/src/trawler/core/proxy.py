"""Range-aware proxying for direct media URLs (preview, thumbnails, subtitles)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from ..config import settings

CLIENT = httpx.AsyncClient(
    timeout=httpx.Timeout(20.0, read=120.0),
    follow_redirects=True,
    limits=httpx.Limits(max_connections=64, max_keepalive_connections=16),
)

PASS_HEADERS = ("content-type", "content-length", "content-range", "accept-ranges", "etag", "last-modified")


async def open_stream(url: str, headers: dict | None, range_header: str | None) -> tuple[httpx.Response, AsyncIterator[bytes]]:
    merged = {"User-Agent": settings.user_agent}
    if headers:
        merged.update({k: v for k, v in headers.items() if k not in ("Accept-Encoding",)})
    if range_header:
        merged["Range"] = range_header
    request = CLIENT.build_request("GET", url, headers=merged)
    response = await CLIENT.send(request, stream=True)
    return response, response.aiter_raw()


def response_headers(response: httpx.Response, content_type: str | None = None) -> dict[str, str]:
    out = {k: v for k, v in response.headers.items() if k.lower() in PASS_HEADERS}
    if content_type:
        out["content-type"] = content_type
    return out
