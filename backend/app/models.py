from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GeoLocation:
    name: str
    lat: float
    lon: float
    country_code: str
    country: str = ""
    admin1: str = ""


@dataclass
class ClimateStats:
    avg_temp_max: float | None = None
    avg_temp_min: float | None = None
    max_temp_peak: float | None = None
    min_temp_peak: float | None = None
    rain_day_probability: float | None = None      # % дней с осадками > 3 мм
    heavy_rain_risk: float | None = None           # % дней с осадками > 15 мм
    storm_wind_risk: float | None = None           # % дней с ветром > 40 км/ч
    avg_radiation_mj: float | None = None
    total_days_sampled: int = 0
    yearly_series: list[dict] = field(default_factory=list)  # по годам для графика
    error: str | None = None


@dataclass
class GeopoliticalRisk:
    article_count: int = 0
    avg_tone: float | None = None
    headlines: list[dict] = field(default_factory=list)  # {title, url, date}
    error: str | None = None


@dataclass
class DisasterAlert:
    event_type: str
    title: str
    severity: str          # Green / Orange / Red
    distance_km: float
    url: str = ""
    from_date: str = ""
    to_date: str = ""


@dataclass
class HolidayInfo:
    name: str
    date: str
    countries: list[str] = field(default_factory=list)
    types: list[str] = field(default_factory=list)
    is_public: bool = True


@dataclass
class IndoorPlace:
    name: str
    category: str          # museum / aquarium / gallery / mall / spa / sports_centre
    category_ru: str
    lat: float
    lon: float
    distance_km: float | None = None
