"""Адаптер Open-Meteo Geocoding API."""
from __future__ import annotations

import logging

from ..config import get_settings
from ..models import GeoLocation
from .base import make_client

logger = logging.getLogger("trisp.adapters.geocoding")


async def geocode(destination: str) -> GeoLocation:
    """Ищет город/курорт через Open-Meteo Geocoding API (language=ru)."""
    settings = get_settings()
    params = {"name": destination, "count": 1, "language": "ru"}

    async with make_client() as client:
        resp = await client.get(settings.geocoding_url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results") or []
    if not results:
        raise LookupError(f"Геокодер не нашёл локацию «{destination}»")

    r = results[0]
    return GeoLocation(
        name=r.get("name", destination),
        lat=float(r["latitude"]),
        lon=float(r["longitude"]),
        country_code=r.get("country_code", ""),
        country=r.get("country", ""),
        admin1=r.get("admin1", ""),
    )
