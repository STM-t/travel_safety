"""Адаптер Open-Meteo Historical Archive API — климатический движок.

Запрашивает дневные данные за окно дат пользователя за последние 10 лет
и рассчитывает вероятностные метрики риска погоды.
"""
from __future__ import annotations

import datetime as dt
import logging
import statistics

from ..config import get_settings
from ..models import ClimateStats
from .base import make_client

logger = logging.getLogger("trisp.adapters.climate")

RAIN_DAY_MM = 3.0     # порог «дождливого» дня
HEAVY_RAIN_MM = 15.0  # порог сильного ливня
STORM_WIND_KMH = 40.0 # порог штормового ветра


async def fetch_climate_stats(
    lat: float,
    lon: float,
    start_date: dt.date,
    end_date: dt.date,
    years_back: int = 10,
) -> ClimateStats:
    """Окно [start_date..end_date] (месяц/день) за последние `years_back` лет."""
    settings = get_settings()
    this_year = dt.date.today().year
    # Берём годы, полностью доступные в архиве (архив отстаёт на ~5 дней)
    hist_years = [y for y in range(this_year - years_back, this_year)
                  if _window_in_past(y, start_date, end_date)]
    if not hist_years:
        # fallback: последние 5 лет до текущего года
        hist_years = list(range(this_year - years_back, this_year))

    stats = ClimateStats()
    all_tmax: list[float] = []
    all_tmin: list[float] = []
    all_rain: list[float] = []
    all_wind: list[float] = []
    all_rad: list[float] = []
    yearly_series: list[dict] = []

    async with make_client() as client:
        tasks = []
        for y in hist_years:
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": f"{y}-{start_date:%m-%d}",
                "end_date": f"{y}-{end_date:%m-%d}",
                "daily": ",".join([
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                    "shortwave_radiation_sum",
                ]),
                "timezone": "auto",
            }
            tasks.append((y, client.get(settings.climate_archive_url, params=params)))

        for y, coro in tasks:
            try:
                resp = await coro
                resp.raise_for_status()
                daily = resp.json().get("daily", {})
            except Exception as exc:  # noqa: BLE001 — частичные данные лучше падения
                logger.warning("Climate archive failed for year %s: %s", y, exc)
                continue

            tmax = _clean(daily.get("temperature_2m_max"))
            tmin = _clean(daily.get("temperature_2m_min"))
            rain = _clean(daily.get("precipitation_sum"), default_zero=True)
            wind = _clean(daily.get("wind_speed_10m_max"))
            rad = _clean(daily.get("shortwave_radiation_sum"), default_zero=True)

            all_tmax += tmax
            all_tmin += tmin
            all_rain += rain
            all_wind += wind
            all_rad += rad

            yearly_series.append({
                "year": y,
                "avg_temp_max": round(statistics.fmean(tmax), 1) if tmax else None,
                "avg_temp_min": round(statistics.fmean(tmin), 1) if tmin else None,
                "rain_days_pct": (
                    round(100.0 * sum(1 for v in rain if v > RAIN_DAY_MM) / len(rain), 1)
                    if rain else None
                ),
                "total_precip_mm": round(sum(rain), 1),
                "max_wind_kmh": round(max(wind), 1) if wind else None,
            })

    if not all_rain or not all_tmax:
        stats.error = "Климатические данные недоступны"
        return stats

    n = len(all_rain)
    stats.total_days_sampled = n
    stats.avg_temp_max = round(statistics.fmean(all_tmax), 1)
    stats.avg_temp_min = round(statistics.fmean(all_tmin), 1) if all_tmin else None
    stats.max_temp_peak = round(max(all_tmax), 1)
    stats.min_temp_peak = round(min(all_tmin), 1) if all_tmin else None
    stats.rain_day_probability = round(
        100.0 * sum(1 for v in all_rain if v > RAIN_DAY_MM) / n, 1)
    stats.heavy_rain_risk = round(
        100.0 * sum(1 for v in all_rain if v > HEAVY_RAIN_MM) / n, 1)
    stats.storm_wind_risk = round(
        100.0 * sum(1 for v in all_wind if v > STORM_WIND_KMH) / len(all_wind), 1
    ) if all_wind else 0.0
    stats.avg_radiation_mj = round(statistics.fmean(all_rad), 1) if all_rad else None
    stats.yearly_series = sorted(yearly_series, key=lambda x: x["year"])
    return stats


def _clean(values, default_zero: bool = False) -> list[float]:
    out = []
    for v in values or []:
        if v is None:
            if default_zero:
                out.append(0.0)
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def _window_in_past(year: int, start: dt.date, end: dt.date) -> bool:
    try:
        end_full = dt.date(year, end.month, end.day)
    except ValueError:
        end_full = dt.date(year, 2, 28)
    return end_full < dt.date.today() - dt.timedelta(days=7)
