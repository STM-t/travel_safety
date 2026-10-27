"""Оркестратор анализа: параллельные вызовы адаптеров, скоринг, AI-вердикт, кэш."""
from __future__ import annotations

import asyncio
import logging

from ..adapters import (
    fetch_climate_stats,
    fetch_disaster_alerts,
    fetch_geopolitical_risk,
    fetch_holiday_overlap,
    fetch_indoor_places,
    geocode,
)
from ..config import get_settings
from ..models import ClimateStats, GeopoliticalRisk
from ..schemas import AnalyzeRequest, AnalyzeResponse
from .ai import synthesize_verdict
from .scoring import compute_score
from .storage import infra

logger = logging.getLogger("trisp.orchestrator")

PLAN_B_RAIN_THRESHOLD = 20.0  # % дождливых дней для авто-триггера Плана Б


async def _safe(coro, name: str, degraded: list[str], default):
    """Graceful degradation: упавший источник не роняет весь отчёт."""
    try:
        return await coro
    except Exception as exc:  # noqa: BLE001
        logger.warning("Source %s failed: %s", name, exc)
        degraded.append(name)
        return default


async def analyze_trip(req: AnalyzeRequest) -> AnalyzeResponse:
    settings = get_settings()
    degraded: list[str] = []

    # --- 1. Геокодинг (блокирующий: всё зависит от координат) ---
    cache_key = infra.report_key(
        req.destination, req.start_date.isoformat(), req.end_date.isoformat(), req.trip_type
    )
    cached = await infra.cache_get(cache_key)
    if cached:
        cached["cached"] = True
        return AnalyzeResponse.model_validate(cached)

    loc_meta = await infra.get_location_meta(req.destination)
    if loc_meta:
        from ..models import GeoLocation
        location = GeoLocation(**loc_meta)
    else:
        location = await _safe(
            geocode(req.destination), "geocoding", degraded, default=None
        )
        if location is None:
            raise LookupError(
                f"Не удалось найти локацию «{req.destination}» (геокодер недоступен)"
            )
        await infra.save_location_meta(req.destination, {
            "name": location.name, "lat": location.lat, "lon": location.lon,
            "country_code": location.country_code, "country": location.country,
            "admin1": location.admin1,
        })

    # --- 2. Параллельные источники данных ---
    climate_task = _safe(
        fetch_climate_stats(location.lat, location.lon, req.start_date, req.end_date),
        "climate", degraded, default=ClimateStats(error="Климат недоступен"),
    )
    geopolitics_task = _safe(
        fetch_geopolitical_risk(location.name or req.destination, location.country_code),
        "gdelt", degraded, default=GeopoliticalRisk(error="GDELT недоступен"),
    )
    disasters_task = _safe(
        fetch_disaster_alerts(location.lat, location.lon),
        "gdacs", degraded, default=[],
    )
    holidays_task = _safe(
        fetch_holiday_overlap(location.country_code, req.start_date, req.end_date),
        "holidays", degraded, default=[],
    )

    climate, geopolitics, disasters, holidays = await asyncio.gather(
        climate_task, geopolitics_task, disasters_task, holidays_task
    )

    # --- 3. Скоринг ---
    score = compute_score(climate, geopolitics, disasters, holidays, req.trip_type)

    # --- 4. План Б: авто-триггер при риске дождя > 20% ---
    rain_pct = climate.rain_day_probability or 0.0
    plan_b_triggered = rain_pct > PLAN_B_RAIN_THRESHOLD
    plan_b = []
    if plan_b_triggered:
        plan_b = await _safe(
            fetch_indoor_places(location.lat, location.lon),
            "overpass", degraded, default=[],
        )

    # --- 5. AI-вердикт ---
    dates_label = f"{req.start_date:%d.%m.%Y} — {req.end_date:%d.%m.%Y}"
    verdict_md, ai_source = await synthesize_verdict(
        location_name=location.name,
        country=location.country,
        dates_label=dates_label,
        trip_type=req.trip_type,
        score=score,
        climate=climate,
        geopolitics=geopolitics,
        disasters=disasters,
        holidays=holidays,
        plan_b=plan_b,
    )

    response = AnalyzeResponse(
        cached=False,
        location={
            "name": location.name, "lat": location.lat, "lon": location.lon,
            "country_code": location.country_code, "country": location.country,
            "admin1": location.admin1,
        },
        score={
            "total": score.total, "climate": score.climate, "safety": score.safety,
            "seasonality": score.seasonality, "verdict": score.verdict,
            "verdict_ru": score.verdict_ru, "notes": score.notes,
        },
        climate=climate.__dict__ | {"yearly_series": climate.yearly_series},
        geopolitics=geopolitics.__dict__,
        disasters=[a.__dict__ for a in disasters],
        holidays=[h.__dict__ for h in holidays],
        plan_b=[p.__dict__ for p in plan_b],
        plan_b_triggered_by_rain=plan_b_triggered,
        ai_verdict_md=verdict_md,
        ai_source=ai_source,
        degraded_sources=degraded,
    )

    # --- 6. Персистентность и кэш ---
    await infra.save_search(
        req.destination, req.start_date, req.end_date, req.trip_type,
        score.total, score.verdict,
    )
    payload = response.model_dump(mode="json")
    payload.pop("cached", None)
    if not degraded:  # не кэшируем частично деградировавшие отчёты
        await infra.cache_set(cache_key, payload)

    return response
