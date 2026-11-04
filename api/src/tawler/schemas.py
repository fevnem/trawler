"""Request models. Responses are assembled in the route modules."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProbeRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
