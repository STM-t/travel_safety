"""Trip Viability Score — математический движок оценки поездки (0–100).

Score = 0.45 * S_climate + 0.35 * S_safety + 0.20 * S_seasonality
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from ..models import ClimateStats, DisasterAlert, GeopoliticalRisk, HolidayInfo

WEIGHT_CLIMATE = 0.45
WEIGHT_SAFETY = 0.35
WEIGHT_SEASONALITY = 0.20


@dataclass
class ScoreBreakdown:
    climate: float
    safety: float
    seasonality: float
    total: float
    verdict: str          # green / yellow / red
    verdict_ru: str
    notes: list[str]


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def score_climate(c: ClimateStats, trip_type: str) -> tuple[float, list[str]]:
    """S_climate: старт 100, штрафы за дожди, ливни, экстремальные температуры, ветер."""
    s = 100.0
    notes: list[str] = []
    if c.error or c.rain_day_probability is None:
        return 60.0, ["Климатические данные неполные — нейтральная оценка"]

    rain = c.rain_day_probability or 0.0
    heavy = c.heavy_rain_risk or 0.0
    wind = c.storm_wind_risk or 0.0

    penalty_rain = rain * 1.2
    s -= penalty_rain
    if rain > 40:
        notes.append(f"Исторически {rain:.0f}% дней в этот период дождливые")

    penalty_heavy = heavy * 1.8
    s -= penalty_heavy
    if heavy > 10:
        notes.append(f"Риск тропических ливней (>15 мм): {heavy:.0f}% дней")

    # Экстремумы температур
    tmax = c.avg_temp_max
    tmin = c.avg_temp_min
    if tmax is not None:
        if tmax > 36:
            s -= (tmax - 36) * 4
            notes.append(f"Экстремальная жара: средний максимум +{tmax:.0f}°C")
        elif trip_type == "beach" and tmax < 26:
            s -= (26 - tmax) * 2.5
            notes.append(f"Для пляжа прохладно: максимум +{tmax:.0f}°C")
    if tmin is not None:
        cold_floor = 18.0 if trip_type == "beach" else 12.0
        if tmin < cold_floor:
            s -= (cold_floor - tmin) * 2.0
            notes.append(f"Холодные ночи: минимум {tmin:.0f}°C")

    # Ветер: для пляжа/гор важнее
    wind_weight = 2.2 if trip_type in ("beach", "mountains") else 1.4
    s -= wind * wind_weight
    if wind > 15:
        notes.append(f"Штормовой ветер (>40 км/ч) в {wind:.0f}% дней")

    # Нестабильность сезона (межгодовой разброс доли дождливых дней)
    if len(c.yearly_series) >= 3:
        pcts = [y["rain_days_pct"] for y in c.yearly_series if y.get("rain_days_pct") is not None]
        if len(pcts) >= 3:
            spread = statistics.pstdev(pcts)
            if spread > 15:
                s -= 5
                notes.append("Высокая межгодовая нестабильность погоды")

    return _clamp(s), notes


def score_safety(g: GeopoliticalRisk, alerts: list[DisasterAlert]) -> tuple[float, list[str]]:
    """S_safety: штрафы за протесты/забастовки GDELT и алерты GDACS."""
    s = 100.0
    notes: list[str] = []

    if g.error:
        s -= 10
        notes.append("Данные GDELT недоступны — запасной штраф")
    else:
        count = g.article_count
        if count >= 40:
            s -= 35
            notes.append(f"Высокий новостной фон протестов/непогод ({count} статей за 30 дней)")
        elif count >= 15:
            s -= 20
            notes.append(f"Замечен рост упоминаний беспорядков ({count} статей за 30 дней)")
        elif count >= 5:
            s -= 10
            notes.append(f"Единичные сообщения о протестах/ЧС ({count} статей)")
        if g.avg_tone is not None and g.avg_tone < -6:
            s -= 8
            notes.append(f"Негативный тональный индекс новостей: {g.avg_tone}")

    for a in alerts:
        if a.severity == "Red":
            s -= 45
            notes.append(f"КРАСНЫЙ алерт GDACS: {a.title} (~{a.distance_km} км)")
        elif a.severity == "Orange":
            s -= 25
            notes.append(f"Оранжевый алерт GDACS: {a.title} (~{a.distance_km} км)")
        else:
            s -= 8
            notes.append(f"Алерт GDACS (зелёный уровень): {a.title} (~{a.distance_km} км)")

    return _clamp(s), notes


def score_seasonality(holidays: list[HolidayInfo], climate: ClimateStats) -> tuple[float, list[str]]:
    """S_seasonality: штрафы за перекрытие с праздниками и сезонную нестабильность."""
    s = 100.0
    notes: list[str] = []

    major_types = {"National holiday", "Religious holiday", "Seasonal"}
    for h in holidays:
        is_major = bool(set(h.types) & major_types)
        s -= 15 if is_major else 8
        notes.append(f"Праздник в даты поездки: {h.name} ({h.date}) — толпы/закрытая инфраструктура")

    # Межгодовая волатильность осадок как признак плечевого сезона
    if len(climate.yearly_series) >= 4:
        precs = [y["total_precip_mm"] for y in climate.yearly_series if y.get("total_precip_mm") is not None]
        if precs and statistics.fmean(precs) > 0:
            cv = statistics.pstdev(precs) / statistics.fmean(precs)
            if cv > 0.6:
                s -= 10
                notes.append("Похоже на плечевой сезон: осадки сильно различаются по годам")

    return _clamp(s), notes


def compute_score(
    climate: ClimateStats,
    geopolitics: GeopoliticalRisk,
    disasters: list[DisasterAlert],
    holidays: list[HolidayInfo],
    trip_type: str,
) -> ScoreBreakdown:
    s_climate, n_climate = score_climate(climate, trip_type)
    s_safety, n_safety = score_safety(geopolitics, disasters)
    s_season, n_season = score_seasonality(holidays, climate)

    total = round(
        WEIGHT_CLIMATE * s_climate + WEIGHT_SAFETY * s_safety + WEIGHT_SEASONALITY * s_season, 1
    )

    if total >= 80:
        verdict, verdict_ru = "green", "Отличное время для поездки"
    elif total >= 50:
        verdict, verdict_ru = "yellow", "Есть скрытые риски: нужен План Б"
    else:
        verdict, verdict_ru = "red", "Высокий риск испорченного отпуска"

    return ScoreBreakdown(
        climate=round(s_climate, 1),
        safety=round(s_safety, 1),
        seasonality=round(s_season, 1),
        total=total,
        verdict=verdict,
        verdict_ru=verdict_ru,
        notes=n_climate + n_safety + n_season,
    )
