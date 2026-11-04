from __future__ import annotations

import anyio
from fastapi import APIRouter, HTTPException

from ..core import limits, ytdlp
from ..schemas import ProbeRequest

router = APIRouter()


@router.post("/probe")
async def probe(body: ProbeRequest) -> dict:
    async with limits.probes:
        try:
            return await anyio.to_thread.run_sync(ytdlp.probe, body.url.strip())
        except ytdlp.ProbeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
