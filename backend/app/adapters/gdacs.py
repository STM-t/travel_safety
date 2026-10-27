"""Адаптер GDACS RSS — природные катаклизмы в радиусе 500 км."""
from __future__ import annotations

import logging
import math

from ..config import get_settings
from ..models import DisasterAlert
from .base import make_client

logger = logging.getLogger("trisp.adapters.gdacs")

RADIUS_KM = 500.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


async def fetch_disaster_alerts(lat: float, lon: float) -> list[DisasterAlert]:
    """Читает GDACS RSS и возвращает активные события в радиусе 500 км."""
    settings = get_settings()
    alerts: list[DisasterAlert] = []

    async with make_client() as client:
        resp = await client.get(settings.gdacs_rss_url)
        resp.raise_for_status()
        raw = resp.content

    # Парсим XML без внешних зависимостей (feedparser как запасной вариант)
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        logger.warning("GDACS RSS parse error: %s", exc)
        return alerts

    ns = {"georss": "http://www.georss.org/georss"}

    for item in root.iter("item"):
        guid = (item.findtext("guid") or "").strip()
        if not guid.startswith("sm:"):
            continue  # только активные события (gdacs:alertlevel в GUID-схеме sm:)
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "")

        severity = "Green"
        for attr_el in item.iter():
            tag = attr_el.tag.split("}")[-1]
            if tag == "alertlevel" and attr_el.text:
                severity = attr_el.text.strip().capitalize()

        event_type = title.split()[0].lower() if title else "event"
        # from/to даты из description (GDACS форматы различаются по типам событий)
        from_date = to_date = ""
        for key in ("FromDate", "ValidFrom", "EqTime", "StartTime"):
            token = f"{key}:"
            if token in desc:
                from_date = desc.split(token)[1][:19].strip()
                break
        for key in ("ToDate", "ValidUntil", "EndTime"):
            token = f"{key}:"
            if token in desc:
                to_date = desc.split(token)[1][:19].strip()
                break

        point = item.find("georss:point", ns)
        if point is None or not (point.text or "").strip():
            continue
        try:
            elat, elon = [float(x) for x in point.text.split()[:2]]
        except ValueError:
            continue

        dist = _haversine_km(lat, lon, elat, elon)
        if dist <= RADIUS_KM:
            alerts.append(DisasterAlert(
                event_type=event_type,
                title=title,
                severity=severity,
                distance_km=round(dist),
                url=link,
                from_date=from_date,
                to_date=to_date,
            ))

    alerts.sort(key=lambda a: ({"Red": 0, "Orange": 1}.get(a.severity, 2), a.distance_km))
    return alerts
