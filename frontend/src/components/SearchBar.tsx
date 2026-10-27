"use client";

import { useState } from "react";
import { Search, MapPin, CalendarDays, Loader2 } from "lucide-react";
import type { AnalyzeRequest } from "@/lib/types";
import { TRIP_TYPES } from "@/lib/format";

interface Props {
  loading: boolean;
  onSubmit: (req: AnalyzeRequest) => void;
}

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export default function SearchBar({ loading, onSubmit }: Props) {
  const today = new Date();
  const defStart = new Date(today.getTime() + 30 * 86400000);
  const defEnd = new Date(today.getTime() + 40 * 86400000);

  const [destination, setDestination] = useState("Phuket");
  const [startDate, setStartDate] = useState(isoDate(defStart));
  const [endDate, setEndDate] = useState(isoDate(defEnd));
  const [tripType, setTripType] = useState<AnalyzeRequest["trip_type"]>("beach");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!destination.trim() || destination.trim().length < 2) {
      setError("Укажите название города или курорта");
      return;
    }
    if (!startDate || !endDate) {
      setError("Укажите даты поездки");
      return;
    }
    if (endDate < startDate) {
      setError("Дата окончания раньше даты начала");
      return;
    }
    onSubmit({
      destination: destination.trim(),
      start_date: startDate,
      end_date: endDate,
      trip_type: tripType,
    });
  }

  const inputCls =
    "w-full rounded-xl border bg-transparent px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500/50";

  return (
    <form onSubmit={handleSubmit} className="card">
      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto_auto_auto] gap-3 items-end">
        <label className="block min-w-[220px]">
          <span className="mb-1 flex items-center gap-1.5 text-xs font-medium muted">
            <MapPin size={14} /> Куда едем
          </span>
          <input
            className={inputCls}
            style={{ borderColor: "var(--border)" }}
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Пхукет, Барселона, Дубай…"
            disabled={loading}
          />
        </label>

        <label className="block">
          <span className="mb-1 flex items-center gap-1.5 text-xs font-medium muted">
            <CalendarDays size={14} /> Заезд
          </span>
          <input
            type="date"
            className={inputCls}
            style={{ borderColor: "var(--border)" }}
            value={startDate}
            max={endDate}
            onChange={(e) => setStartDate(e.target.value)}
            disabled={loading}
          />
        </label>

        <label className="block">
          <span className="mb-1 flex items-center gap-1.5 text-xs font-medium muted">
            <CalendarDays size={14} /> Выезд
          </span>
          <input
            type="date"
            className={inputCls}
            style={{ borderColor: "var(--border)" }}
            value={endDate}
            min={startDate}
            onChange={(e) => setEndDate(e.target.value)}
            disabled={loading}
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-medium muted">Тип поездки</span>
          <select
            className={inputCls}
            style={{ borderColor: "var(--border)" }}
            value={tripType}
            onChange={(e) =>
              setTripType(e.target.value as AnalyzeRequest["trip_type"])
            }
            disabled={loading}
          >
            {TRIP_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          disabled={loading}
          className="inline-flex h-[42px] items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-60"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" /> Анализируем…
            </>
          ) : (
            <>
              <Search size={16} /> Анализировать
            </>
          )}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      <p className="mt-2 text-xs muted">
        Сервис агрегирует климатическую статистику за 10 лет, новости GDELT,
        алерты GDACS и праздники — анализ может занять 10–30 секунд.
      </p>
    </form>
  );
}
