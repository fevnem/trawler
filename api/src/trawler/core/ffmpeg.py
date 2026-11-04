"""ffmpeg argv builders and the pipe runner.

Nothing is written to disk. ffmpeg reads remote URLs and writes the container to
stdout, which is the HTTP response body.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

FFMPEG = "ffmpeg"

AUDIO_TARGETS = {
    "mp3": ["-c:a", "libmp3lame", "-b:a", "192k", "-f", "mp3"],
    "m4a": ["-c:a", "aac", "-b:a", "192k", "-movflags", "+frag_keyframe+empty_moov", "-f", "mp4"],
    "opus": ["-c:a", "libopus", "-b:a", "128k", "-f", "ogg"],
    "wav": ["-c:a", "pcm_s16le", "-f", "wav"],
    "flac": ["-c:a", "flac", "-f", "flac"],
}


def _headers(values: dict | None) -> list[str]:
    if not values:
        return []
    blob = "".join(f"{k}: {v}\r\n" for k, v in values.items())
    return ["-headers", blob]


def _base() -> list[str]:
    return [FFMPEG, "-hide_banner", "-loglevel", "error", "-nostdin"]


def merge(video_url: str, audio_url: str | None, headers: dict | None, container: str,
          start: float | None, end: float | None) -> list[str]:
    args = _base()
    if start:
        args += ["-ss", f"{start:.3f}"]
    args += _headers(headers) + ["-i", video_url]
    if audio_url:
        args += _headers(headers) + ["-i", audio_url]
    if start and end:
        args += ["-t", f"{max(end - start, 0.1):.3f}"]
    args += ["-map", "0:v:0"]
    if audio_url:
        args += ["-map", "1:a:0"]
    args += ["-c", "copy", "-avoid_negative_ts", "make_zero"]
    if container == "webm":
        args += ["-f", "webm"]
    else:
        args += ["-movflags", "+frag_keyframe+empty_moov+default_base_moof", "-f", "mp4"]
    return args + ["pipe:1"]


def transcode_audio(url: str, headers: dict | None, target: str,
                    start: float | None, end: float | None) -> list[str]:
    args = _base()
    if start:
        args += ["-ss", f"{start:.3f}"]
    args += _headers(headers) + ["-i", url]
    if start and end:
        args += ["-t", f"{max(end - start, 0.1):.3f}"]
    args += ["-vn"] + AUDIO_TARGETS.get(target, AUDIO_TARGETS["mp3"])
    return args + ["pipe:1"]


def gif(url: str, headers: dict | None, start: float, duration: float,
        width: int, fps: int) -> list[str]:
    filters = (
        f"[0:v]fps={fps},scale={width}:-1:flags=lanczos,split[a][b];"
        f"[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5"
    )
    args = _base()
    args += ["-ss", f"{start:.3f}", "-t", f"{duration:.3f}"]
    args += _headers(headers) + ["-i", url]
    args += ["-filter_complex", filters, "-loop", "0", "-f", "gif", "pipe:1"]
    return args


class PipeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


async def run(args: list[str]) -> AsyncGenerator[bytes, None]:
    """Start ffmpeg and yield stdout. Fails loudly if the first byte never comes."""
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.DEVNULL,
    )
    stderr_chunks: list[bytes] = []

    async def drain() -> None:
        assert proc.stderr is not None
        while True:
            chunk = await proc.stderr.read(4096)
            if not chunk:
                return
            if sum(len(c) for c in stderr_chunks) < 8192:
                stderr_chunks.append(chunk)

    drainer = asyncio.create_task(drain())
    try:
        assert proc.stdout is not None
        first = await proc.stdout.read(65536)
        if not first:
            await proc.wait()
            await drainer
            detail = b"".join(stderr_chunks).decode("utf-8", "replace").strip()
            raise PipeError(detail.splitlines()[-1][:240] if detail else "ffmpeg produced no output")
        yield first
        while True:
            chunk = await proc.stdout.read(262144)
            if not chunk:
                break
            yield chunk
    finally:
        if proc.returncode is None:
            proc.kill()
        await proc.wait()
        drainer.cancel()
