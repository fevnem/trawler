from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .config import settings
from .routes import catalog, media, probe

app = FastAPI(title="trawler api", docs_url="/api/docs", openapi_url="/api/openapi.json")

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
