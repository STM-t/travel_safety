"""Адаптер Nager.Date — государственные праздники и проверка перекрытия дат."""
from __future__ import annotations

import datetime as dt
import logging

from ..config import get_settings
from ..models import HolidayInfo
from .base import make_client

logger = logging.getLogger("trisp.adapters.holidays")


async def fetch_holiday_overlap(
    country_code: str, start_date: dt.date, end_date: dt.date
) -> list[HolidayInfo]:
    """Возвращает публичные праздники страны, попадающие в окно поездки."""
    settings = get_settings()
    if not country_code:
        return []

    holidays: list[HolidayInfo] = []
    async with make_client() as client:
        for year in range(start_date.year, end_date.year + 1):
            url = settings.nager_holidays_url_template.format(
                year=year, country_code=country_code
            )
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Nager.Date failed for %s/%s: %s", year, country_code, exc)
                continue

            for h in data:
                try:
                    hdate = dt.date.fromisoformat(h["date"])
                except (KeyError, ValueError):
                    continue
                if start_date <= hdate <= end_date and h.get("public", True):
                    holidays.append(HolidayInfo(
                        name=h.get("name", ""),
                        date=h["date"],
                        countries=[h.get("countryCode", country_code)],
                        types=h.get("types", []),
                        is_public=bool(h.get("public", True)),
                    ))
    return holidays
