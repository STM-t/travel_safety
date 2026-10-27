// Типы, зеркаляющие backend/app/schemas.py (AnalyzeResponse)

export interface AnalyzeRequest {
  destination: string;
  start_date: string; // YYYY-MM-DD
  end_date: string;
  trip_type: "beach" | "tours" | "mountains";
}

export interface LocationOut {
  name: string;
  lat: number;
  lon: number;
  country_code: string;
  country: string;
  admin1: string;
}

export interface YearlyPoint {
  year: number;
  avg_temp_max: number | null;
  avg_temp_min: number | null;
  rain_days_pct: number | null;
  total_precip_mm: number | null;
  max_wind_kmh: number | null;
}

export interface ClimateOut {
  avg_temp_max: number | null;
  avg_temp_min: number | null;
  max_temp_peak: number | null;
  min_temp_peak: number | null;
  rain_day_probability: number | null;
  heavy_rain_risk: number | null;
  storm_wind_risk: number | null;
  avg_radiation_mj: number | null;
  total_days_sampled: number;
  yearly_series: YearlyPoint[];
  error: string | null;
}

export interface HeadlineOut {
  title: string;
  url: string;
  date: string;
  source: string;
  tone: string | number;
}

export interface GeopoliticsOut {
  article_count: number;
  avg_tone: number | null;
  headlines: HeadlineOut[];
  error: string | null;
}

export interface DisasterOut {
  event_type: string;
  title: string;
  severity: string; // Red / Orange / Green
  distance_km: number;
  url: string;
  from_date: string;
  to_date: string;
}

export interface HolidayOut {
  name: string;
  date: string;
  countries: string[];
  types: string[];
  is_public: boolean;
}

export interface PlaceOut {
  name: string;
  category: string;
  category_ru: string;
  lat: number;
  lon: number;
  distance_km: number | null;
}

export interface ScoreOut {
  total: number;
  climate: number;
  safety: number;
  seasonality: number;
  verdict: "green" | "yellow" | "red";
  verdict_ru: string;
  notes: string[];
}

export interface AnalyzeResponse {
  cached: boolean;
  location: LocationOut;
  score: ScoreOut;
  climate: ClimateOut;
  geopolitics: GeopoliticsOut;
  disasters: DisasterOut[];
  holidays: HolidayOut[];
  plan_b: PlaceOut[];
  plan_b_triggered_by_rain: boolean;
  ai_verdict_md: string;
  ai_source: string;
  degraded_sources: string[];
}
