from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .config import settings
from .core.throttle import ThrottleMiddleware
from .mcp_server import build_app as build_mcp_app
from .mcp_server import mcp_lifespan
from .routes import catalog, media, probe


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with mcp_lifespan():
        yield


app = FastAPI(
    title="trawler api",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=2048)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["content-length", "content-range", "content-disposition"],
)

app.include_router(catalog.router, prefix="/api", tags=["catalog"])
app.include_router(probe.router, prefix="/api", tags=["probe"])
app.include_router(media.router, prefix="/api", tags=["media"])

# Added last so it runs first: the limiter must decide before any work starts.
app.add_middleware(ThrottleMiddleware)

# MCP rides the same /api rewrite the browser already uses. Mounting at /api with
# the inner route at /mcp avoids the trailing-slash redirect a root mount would emit.
_mcp = build_mcp_app("/mcp")
if _mcp is not None:
    app.mount("/api", _mcp)
