"""Every byte the browser receives passes through here, and nothing touches disk."""

from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import quote

import anyio
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..core import ffmpeg, limits, proxy, tickets

router = APIRouter()


def _ticket(token: str) -> dict:
    try:
        return tickets.verify(token)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _disposition(filename: str, inline: bool = False) -> str:
    kind = "inline" if inline else "attachment"
    return f"{kind}; filename*=UTF-8''{quote(filename)}"


async def _proxy(url: str, headers: dict | None, range_header: str | None,
                 filename: str | None, content_type: str | None, inline: bool) -> StreamingResponse:
    try:
        response, iterator = await proxy.open_stream(url, headers, range_header)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Upstream refused the request.") from exc
    if response.status_code >= 400:
        await response.aclose()
        raise HTTPException(status_code=502, detail=f"Upstream returned {response.status_code}.")

    out = proxy.response_headers(response, content_type)
    if filename:
        out["content-disposition"] = _disposition(filename, inline)
    out.setdefault("accept-ranges", "bytes")

    async def body() -> AsyncIterator[bytes]:
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await response.aclose()

    return StreamingResponse(body(), status_code=response.status_code, headers=out)


async def _pipe(args: list[str], media_type: str, filename: str) -> StreamingResponse:
    stream = ffmpeg.run(args)
    try:
        first = await stream.__anext__()
    except ffmpeg.PipeError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc
    except StopAsyncIteration as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail="No output.") from exc

    async def body() -> AsyncIterator[bytes]:
        try:
            yield first
            async for chunk in stream:
                yield chunk
        finally:
            await stream.aclose()

    headers = {"content-disposition": _disposition(filename), "cache-control": "no-store"}
    return StreamingResponse(body(), media_type=media_type, headers=headers)


@router.get("/thumb/{token}")
async def thumb(token: str, request: Request) -> StreamingResponse:
    data = _ticket(token)
    if data.get("k") != "t":
        raise HTTPException(status_code=400, detail="Wrong ticket kind.")
    return await _proxy(data["u"], data.get("h"), None, None, None, True)


@router.get("/sub/{token}")
async def subtitle(token: str) -> StreamingResponse:
    data = _ticket(token)
    if data.get("k") != "s":
        raise HTTPException(status_code=400, detail="Wrong ticket kind.")
    ext = data.get("x", "vtt")
    return await _proxy(data["u"], data.get("h"), None, f"subtitles.{ext}",
                        "text/vtt; charset=utf-8", False)


@router.get("/preview/{token}")
async def preview(token: str, request: Request) -> StreamingResponse:
    data = _ticket(token)
    if data.get("k") not in ("m", "v", "a"):
        raise HTTPException(status_code=400, detail="Wrong ticket kind.")
    if data["k"] in ("m", "a") and data.get("p") in ("http", "https", None):
        return await _proxy(data["u"], data.get("h"), request.headers.get("range"), None, None, True)
    async with limits.downloads:
        args = ffmpeg.merge(data["u"], data.get("a"), data.get("h"), data.get("x", "mp4"), None, None)
        return await _pipe(args, f"video/{data.get('x', 'mp4')}", "preview." + data.get("x", "mp4"))


@router.get("/dl/{token}")
async def download(
    token: str,
    request: Request,
    start: float | None = Query(default=None, ge=0, le=86400),
    end: float | None = Query(default=None, ge=0, le=86400),
    to: str | None = Query(default=None, max_length=8),
) -> StreamingResponse:
    data = _ticket(token)
    kind = data.get("k")

    if kind == "m" and not start and data.get("p") in ("http", "https", None):
        return await _proxy(data["u"], data.get("h"), request.headers.get("range"),
                            data.get("n"), None, False)

    if kind in ("m", "v"):
        container = data.get("x", "mp4")
        async with limits.downloads:
            args = ffmpeg.merge(data["u"], data.get("a"), data.get("h"), container, start, end)
            return await _pipe(args, f"video/{container}", data.get("n") or f"video.{container}")

    if kind == "a":
        target = (to or data.get("x") or "mp3").lower()
        if target not in ffmpeg.AUDIO_TARGETS:
            target = "mp3"
        name = (data.get("n") or "audio").rsplit(".", 1)[0] + "." + target
        async with limits.downloads:
            args = ffmpeg.transcode_audio(data["u"], data.get("h"), target, start, end)
            return await _pipe(args, f"audio/{target}", name)

    raise HTTPException(status_code=400, detail="Wrong ticket kind.")


@router.get("/gif/{token}")
async def gif(
    token: str,
    start: float = Query(default=0, ge=0, le=86400),
    end: float = Query(default=5, ge=0, le=86400),
    width: int = Query(default=480, ge=120, le=960),
    fps: int = Query(default=12, ge=4, le=30),
) -> StreamingResponse:
    data = _ticket(token)
    if data.get("k") not in ("m", "v"):
        raise HTTPException(status_code=400, detail="Wrong ticket kind.")
    span = max(min(end - start, 30.0), 0.2)
    name = (data.get("n") or "clip").rsplit(".", 1)[0] + ".gif"
    async with limits.downloads:
        args = ffmpeg.gif(data["u"], data.get("h"), start, span, width, fps)
        return await _pipe(args, "image/gif", name)
