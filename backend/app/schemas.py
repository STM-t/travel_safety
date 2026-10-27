"""Pydantic-схемы API."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalyzeRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=120, examples=["Phuket"])
    start_date: date
    end_date: date
    trip_type: Literal["beach", "tours", "mountains"] = "tours"

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date раньше start_date")
        if (self.end_date - self.start_date).days > 90:
            raise ValueError("Максимальная длительность окна — 90 дней")
        return self


class LocationOut(BaseModel):
    name: str
    lat: float
    lon: float
    country_code: str
    country: str
    admin1: str


class YearlyPoint(BaseModel):
    year: int
    avg_temp_max: float | None = None
    avg_temp_min: float | None = None
    rain_days_pct: float | None = None
    total_precip_mm: float | None = None
    max_wind_kmh: float | None = None


class ClimateOut(BaseModel):
    avg_temp_max: float | None = None
    avg_temp_min: float | None = None
    max_temp_peak: float | None = None
    min_temp_peak: float | None = None
    rain_day_probability: float | None = None
    heavy_rain_risk: float | None = None
    storm_wind_risk: float | None = None
    avg_radiation_mj: float | None = None
    total_days_sampled: int = 0
    yearly_series: list[YearlyPoint] = []
    error: str | None = None


class HeadlineOut(BaseModel):
    title: str
    url: str
    date: str = ""
    source: str = ""
    tone: str | float = ""


class GeopoliticsOut(BaseModel):
    article_count: int = 0
    avg_tone: float | None = None
    headlines: list[HeadlineOut] = []
    error: str | None = None


class DisasterOut(BaseModel):
    event_type: str
    title: str
    severity: str
    distance_km: float
    url: str = ""
    from_date: str = ""
    to_date: str = ""


class HolidayOut(BaseModel):
    name: str
    date: str
    countries: list[str] = []
    types: list[str] = []
    is_public: bool = True


class PlaceOut(BaseModel):
    name: str
    category: str
    category_ru: str
    lat: float
    lon: float
    distance_km: float | None = None


class ScoreOut(BaseModel):
    total: float
    climate: float
    safety: float
    seasonality: float
    verdict: str
    verdict_ru: str
    notes: list[str] = []


class AnalyzeResponse(BaseModel):
    cached: bool = False
    location: LocationOut
    score: ScoreOut
    climate: ClimateOut
    geopolitics: GeopoliticsOut
    disasters: list[DisasterOut] = []
    holidays: list[HolidayOut] = []
    plan_b: list[PlaceOut] = []
    plan_b_triggered_by_rain: bool = False
    ai_verdict_md: str
    ai_source: str  # llm / fallback
    degraded_sources: list[str] = []
