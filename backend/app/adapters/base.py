"""Базовый HTTP-клиент с таймаутом и graceful degradation."""
from __future__ import annotations

import logging

import httpx

from ..config import get_settings

logger = logging.getLogger("trisp.adapters")

CLIENT_KWARGS = {
    "timeout": httpx.Timeout(get_settings().http_timeout_seconds, connect=5.0),
    "follow_redirects": True,
    "headers": {"User-Agent": "TravelRiskIntelligencePlatform/1.0 (MVP)"},
}


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(**CLIENT_KWARGS)


async def request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    retries: int = 3,
    backoff: float = 2.0,
    **kwargs,
) -> httpx.Response:
    """Запрос с экспоненциальным бэкоффом на 429/5xx (GDELT rate limit, Overpass capacity)."""
    import asyncio

    last_exc: Exception | None = None
    resp: httpx.Response | None = None
    for attempt in range(retries):
        try:
            resp = await client.request(method, url, **kwargs)
            if resp.status_code in (429, 502, 503, 504) and attempt < retries - 1:
                await asyncio.sleep(backoff * (2 ** attempt))
                continue
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError:
            raise
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt < retries - 1:
                await asyncio.sleep(backoff * (attempt + 1))
    if resp is not None:
        resp.raise_for_status()
    assert last_exc is not None
    raise last_exc
