"""Stateless signed tickets.

Every media URL handed to the browser is wrapped in an HMAC ticket. The API never
accepts a raw URL on a streaming endpoint, so it cannot be used as an open proxy.
Nothing is stored: the payload carries what the request needs and expires.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import zlib

from ..config import settings

_FALLBACK = secrets.token_urlsafe(32)


def _key() -> bytes:
    return (settings.secret or _FALLBACK).encode()


def sign(payload: dict, ttl: int | None = None) -> str:
    body = dict(payload)
    body["e"] = int(time.time()) + (ttl or settings.token_ttl)
    raw = json.dumps(body, separators=(",", ":")).encode()
    blob = base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode().rstrip("=")
    sig = hmac.new(_key(), blob.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{blob}.{sig}"


def verify(token: str) -> dict:
    blob, _, sig = token.partition(".")
    if not blob or not sig:
        raise ValueError("malformed ticket")
    expected = hmac.new(_key(), blob.encode(), hashlib.sha256).hexdigest()[:24]
    if not hmac.compare_digest(sig, expected):
        raise ValueError("bad signature")
    pad = "=" * (-len(blob) % 4)
    try:
        data = json.loads(zlib.decompress(base64.urlsafe_b64decode(blob + pad)))
    except Exception as exc:  # noqa: BLE001
        raise ValueError("unreadable ticket") from exc
    if int(data.get("e", 0)) < time.time():
        raise ValueError("ticket expired")
    return data
