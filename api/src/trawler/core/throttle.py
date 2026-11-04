"""Per-client throttling.

Not DDoS protection — Cloudflare absorbs volume before it reaches us. This exists
for the case that actually happens: one client looping probe or download requests
until the ffmpeg slots are gone.

A token window per client per endpoint class, with escalating cooldowns for repeat
offenders. In-process, like the rest of the state in this app.
"""

from __future__ import annotations

import ipaddress
import json
import time
from collections import deque
from dataclasses import dataclass, field

from ..config import settings

WINDOW = 60.0
# A client that keeps pushing after being told to stop gets progressively longer
# cooldowns instead of a flat one.
BAN_STEPS = (60, 300, 1800, 7200)
MAX_CLIENTS = 20_000


def classify(path: str) -> str:
    if path == "/api/probe":
        return "probe"
    if path == "/api/mcp":
        return "mcp"
    if path.startswith("/api/preview"):
        # A <video> element fires a burst of range requests; count these generously.
        return "preview"
    if path.startswith(("/api/dl", "/api/gif", "/api/sub", "/api/thumb")):
        return "media"
    return "read"


def client_ip(scope) -> str:
    """Real client address.

    The API is only reachable from the web container, which sits behind Traefik and
    Cloudflare, so the proxy headers are the only honest source here.
    """
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    for key in ("cf-connecting-ip", "x-real-ip"):
        value = headers.get(key)
        if value:
            return value.strip()
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


@dataclass
class Client:
    hits: dict[str, deque] = field(default_factory=dict)
    breaches: deque = field(default_factory=deque)
    blocked_until: float = 0.0
    seen: float = field(default_factory=time.monotonic)


class Throttle:
    def __init__(self, limits: dict[str, int]):
        self.limits = limits
        self.clients: dict[str, Client] = {}

    def _client(self, ip: str) -> Client:
        client = self.clients.get(ip)
        if client is None:
            if len(self.clients) >= MAX_CLIENTS:
                self._evict()
            client = Client()
            self.clients[ip] = client
        client.seen = time.monotonic()
        return client

    def _evict(self) -> None:
        """Drop the least recently seen tenth when the table gets large."""
        ordered = sorted(self.clients.items(), key=lambda item: item[1].seen)
        for ip, _ in ordered[: max(1, len(ordered) // 10)]:
            self.clients.pop(ip, None)

    def check(self, ip: str, kind: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        client = self._client(ip)

        if client.blocked_until > now:
            return False, max(1, int(client.blocked_until - now))

        limit = self.limits.get(kind, 60)
        window = client.hits.setdefault(kind, deque())
        while window and now - window[0] > WINDOW:
            window.popleft()

        if len(window) < limit:
            window.append(now)
            return True, 0

        # Breached. Escalate if this client has done it recently.
        while client.breaches and now - client.breaches[0] > 3600:
            client.breaches.popleft()
        step = BAN_STEPS[min(len(client.breaches), len(BAN_STEPS) - 1)]
        client.breaches.append(now)
        client.blocked_until = now + step
        client.hits[kind] = deque()
        return False, step

    def snapshot(self) -> dict[str, int]:
        return {"clients": len(self.clients), "blocked": sum(1 for c in self.clients.values() if c.blocked_until > time.monotonic())}


def is_internal(ip: str) -> bool:
    """Private, loopback or unparseable addresses are never throttled.

    Server-side renders (the web container calling /api/health) arrive from a private
    address on the Compose network. Throttling that would take the site down.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return addr.is_private or addr.is_loopback or addr.is_link_local


class ThrottleMiddleware:
    def __init__(self, app):
        self.app = app
        self.limiter = Throttle(
            {
                "probe": settings.rate_probe,
                "media": settings.rate_media,
                "preview": settings.rate_preview,
                "read": settings.rate_read,
                "mcp": settings.rate_mcp,
            }
        )

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or not scope.get("path", "").startswith("/api"):
            await self.app(scope, receive, send)
            return

        ip = client_ip(scope)
        if is_internal(ip):
            await self.app(scope, receive, send)
            return

        allowed, retry = self.limiter.check(ip, classify(scope["path"]))
        if allowed:
            await self.app(scope, receive, send)
            return

        body = json.dumps(
            {"detail": f"Too many requests from this address. Try again in {retry} seconds."}
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", str(retry).encode()),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
