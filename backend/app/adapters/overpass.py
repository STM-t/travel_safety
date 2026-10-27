"""Адаптер OpenStreetMap Overpass API — «План Б» (крытые места при дожде)."""
from __future__ import annotations

import logging

import httpx

from ..config import get_settings
from ..models import IndoorPlace
from .base import make_client, request_with_retry

logger = logging.getLogger("trisp.adapters.overpass")

# Зеркала Overpass: основной сервер + резервные (защита от 502 at-capacity)
OVERPASS_MIRRORS_FALLBACK = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

# Отдельный увеличенный таймаут для тяжёлых geo-запросов Overpass
OVERPASS_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

CATEGORY_RU = {
    "museum": "Музей",
    "aquarium": "Океанариум",
    "gallery": "Галерея",
    "mall": "Торговый центр",
    "spa": "СПА",
    "sports_centre": "Спортивный центр",
}

RADIUS_M = 15_000  # 15 км


def _build_query(lat: float, lon: float) -> str:
    parts = [
        f'nw["tourism"~"^(museum|aquarium|gallery)$"](around:{RADIUS_M},{lat},{lon});',
        f'nw["shop"="mall"](around:{RADIUS_M},{lat},{lon});',
        f'nw["leisure"~"^(spa|sports_centre)$"](around:{RADIUS_M},{lat},{lon});',
    ]
    return "[out:json][timeout:20];(" + "".join(parts) + ");out center tags 60;"


async def fetch_indoor_places(lat: float, lon: float) -> list[IndoorPlace]:
    """Топ-6 крытых POI в радиусе 15 км от точки (с перебором зеркал Overpass)."""
    settings = get_settings()
    query = _build_query(lat, lon)

    elements: list[dict] = []
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=OVERPASS_TIMEOUT, follow_redirects=True,
                                 headers={"User-Agent": "TravelRiskIntelligencePlatform/1.0 (MVP)"}) as client:
        for url in [settings.overpass_url, *OVERPASS_MIRRORS_FALLBACK]:
            try:
                resp = await request_with_retry(
                    client, "POST", url,
                    data={"data": query},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    retries=2, backoff=3.0,
                )
                elements = resp.json().get("elements", [])
                break
            except Exception as exc:  # noqa: BLE001 — пробуем следующее зеркало
                last_error = exc
                logger.warning("Overpass mirror %s failed: %s", url, repr(exc)[:150])
        if not elements and last_error is not None:
            raise last_error

    places: list[IndoorPlace] = []
    seen: set[str] = set()
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or tags.get("int_name")
        if not name:
            continue
        category = (
            tags.get("tourism")
            or ("mall" if tags.get("shop") == "mall" else None)
            or tags.get("leisure")
        )
        if category not in CATEGORY_RU:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        lat_c = el.get("lat") or (el.get("center") or {}).get("lat")
        lon_c = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat_c is None or lon_c is None:
            continue
        places.append(IndoorPlace(
            name=name,
            category=category,
            category_ru=CATEGORY_RU[category],
            lat=float(lat_c),
            lon=float(lon_c),
        ))

    # Сортировка по расстоянию, топ-6
    from .gdacs import _haversine_km
    for p in places:
        p.distance_km = round(_haversine_km(lat, lon, p.lat, p.lon), 1)
    places.sort(key=lambda p: p.distance_km or 999)
    return places[:6]
