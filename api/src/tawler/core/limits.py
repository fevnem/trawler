"""Concurrency guards. The API runs as one process with fixed worker counts."""

from __future__ import annotations

import anyio

from ..config import settings

downloads = anyio.CapacityLimiter(settings.max_downloads)
probes = anyio.CapacityLimiter(settings.max_probes)
