"use client";

import { useState } from "react";
import { Compass, Globe2 } from "lucide-react";
import SearchBar from "@/components/SearchBar";
import ScoreGauge from "@/components/ScoreGauge";
import ClimateBlock from "@/components/ClimateBlock";
import RiskFeed from "@/components/RiskFeed";
import AiVerdict from "@/components/AiVerdict";
import PlanB from "@/components/PlanB";
import SkeletonReport from "@/components/SkeletonReport";
import ThemeToggle from "@/components/ThemeToggle";
import { analyzeTrip } from "@/lib/api";
import type { AnalyzeRequest, AnalyzeResponse } from "@/lib/types";

const SOURCE_RU: Record<string, string> = {
  open_meteo_geocoding: "геокодинг",
  open_meteo_archive: "климат",
  gdelt: "новости GDELT",
  gdacs: "алерты GDACS",
  nager_date: "праздники",
  overpass: "карта OSM",
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(req: AnalyzeRequest) {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeTrip(req);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось выполнить анализ");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600 text-white">
            <Compass size={24} />
          </div>
          <div>
            <h1 className="text-xl font-extrabold leading-tight">TRISP</h1>
            <p className="text-xs muted">
              Радар рисков и сезонности для путешественников
            </p>
          </div>
        </div>
        <ThemeToggle />
      </header>

      <SearchBar loading={loading} onSubmit={handleSubmit} />

      {error && (
        <div className="mt-5 rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-500">
          ⚠️ {error}. Попробуйте другой запрос — внешние API могут быть временно
          недоступны.
        </div>
      )}

      {loading && (
        <div className="mt-5 space-y-5">
          <div className="flex items-center gap-2 text-sm muted">
            <Globe2 size={16} className="animate-pulse" />
            Собираем данные из 6 источников: климат за 10 лет, GDELT, GDACS,
            праздники, крытые места…
          </div>
          <SkeletonReport />
        </div>
      )}

      {!loading && data && (
        <section className="mt-5 space-y-5">
          {data.degraded_sources.length > 0 && (
            <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-600">
              Частичная деградация данных:{" "}
              {data.degraded_sources
                .map((s) => SOURCE_RU[s] ?? s)
                .join(", ")}{" "}
              — источник недоступен, отчёт построен на остальных данных.
            </div>
          )}

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <ScoreGauge
              score={data.score}
              locationName={data.location.name}
              country={data.location.country}
              cached={data.cached}
            />
            <AiVerdict data={data} />
          </div>

          <ClimateBlock climate={data.climate} />

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <RiskFeed
              geopolitics={data.geopolitics}
              disasters={data.disasters}
              holidays={data.holidays}
            />
            <PlanB
              places={data.plan_b}
              location={data.location}
              triggeredByRain={data.plan_b_triggered_by_rain}
            />
          </div>
        </section>
      )}

      {!loading && !data && !error && (
        <div className="mt-10 text-center">
          <p className="text-sm muted">
            Введите направление и даты — платформа честно оценит риски поездки,
            а не продаст вам мечту ✈️
          </p>
        </div>
      )}

      <footer className="mt-10 border-t pt-4 text-center text-xs muted" style={{ borderColor: "var(--border)" }}>
        Данные: Open-Meteo · GDELT · GDACS · Nager.Date · OpenStreetMap. Сервис —
        «адвокат путешественника», а не агрегатор бронирования.
      </footer>
    </main>
  );
}
