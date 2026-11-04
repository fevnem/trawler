from __future__ import annotations

from fastapi import APIRouter

from ..core import catalog

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"ok": True, "extractors": len(catalog.catalog())}


@router.get("/sites")
def sites(q: str | None = None) -> dict:
    items = catalog.catalog()
    if q:
        needle = q.lower()
        items = [s for s in items if needle in s["name"].lower() or needle in (s["domain"] or "")]
    return {"count": len(catalog.catalog()), "shown": len(items), "sites": items}


@router.get("/match")
def match(url: str) -> dict:
    return {"name": catalog.match(url)}
