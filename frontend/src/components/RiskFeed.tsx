"use client";

import { AlertTriangle, Newspaper, CalendarX2, ExternalLink, ShieldAlert } from "lucide-react";
import type { GeopoliticsOut, DisasterOut, HolidayOut } from "@/lib/types";
import { fmtDateRu } from "@/lib/format";

interface Props {
  geopolitics: GeopoliticsOut;
  disasters: DisasterOut[];
  holidays: HolidayOut[];
}

const SEVERITY_COLORS: Record<string, string> = {
  red: "#ef4444",
  orange: "#f97316",
  green: "#22c55e",
};

const EVENT_RU: Record<string, string> = {
  TC: "Тропический циклон",
  EQ: "Землетрясение",
  FL: "Наводнение",
  WF: "Лесной пожар",
  VO: "Вулкан",
  TS: "Цунами",
  LW: "Морская волна / шторм",
  EX: "Экстремальная температура",
};

export default function RiskFeed({ geopolitics, disasters, holidays }: Props) {
  const tone = geopolitics.avg_tone;
  return (
    <div className="card">
      <h3 className="mb-4 flex items-center gap-2 text-lg font-bold">
        <ShieldAlert size={18} className="text-red-500" /> Геополитика и алерты
      </h3>

      {/* GDACS стихийные бедствия */}
      <section className="mb-5">
        <h4 className="mb-2 text-sm font-semibold muted">
          Стихийные бедствия (GDACS, радиус 500 км)
        </h4>
        {disasters.length === 0 ? (
          <p className="rounded-lg bg-emerald-500/10 px-3 py-2 text-sm text-emerald-600">
            Активных красных/оранжевых алертов не обнаружено ✅
          </p>
        ) : (
          <ul className="space-y-2">
            {disasters.map((d, i) => (
              <li
                key={i}
                className="flex items-start gap-3 rounded-xl border p-3"
                style={{ borderColor: "var(--border)" }}
              >
                <span
                  className="mt-1 inline-block h-3 w-3 shrink-0 rounded-full"
                  style={{
                    background: SEVERITY_COLORS[d.severity?.toLowerCase()] ?? "#eab308",
                  }}
                />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">
                    {EVENT_RU[d.event_type] ?? d.event_type}: {d.title}
                  </p>
                  <p className="text-xs muted">
                    Уровень: {d.severity} · ~{Math.round(d.distance_km)} км от точки ·{" "}
                    {fmtDateRu(d.from_date)}
                  </p>
                  {d.url && (
                    <a
                      href={d.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 inline-flex items-center gap-1 text-xs text-indigo-500 hover:underline"
                    >
                      Источник <ExternalLink size={12} />
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* GDELT новости */}
      <section className="mb-5">
        <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold muted">
          <Newspaper size={14} /> Протесты / забастовки / беспорядки (GDELT, 30 дней)
        </h4>
        {geopolitics.error ? (
          <p className="text-sm muted">Данные GDELT временно недоступны.</p>
        ) : (
          <>
            <p className="mb-2 text-sm">
              Упоминаний: <b>{geopolitics.article_count}</b>
              {tone != null && (
                <>
                  {" "}· Тон новостей:{" "}
                  <b style={{ color: tone < -3 ? "#ef4444" : tone < 0 ? "#eab308" : "#22c55e" }}>
                    {tone.toFixed(2)}
                  </b>
                </>
              )}
            </p>
            {geopolitics.headlines.length > 0 && (
              <ul className="space-y-1.5">
                {geopolitics.headlines.slice(0, 5).map((h, i) => (
                  <li key={i} className="text-sm leading-snug">
                    <a
                      href={h.url}
                      target="_blank"
                      rel="noreferrer"
                      className="hover:underline"
                    >
                      {h.title}
                    </a>
                    <span className="ml-1 text-xs muted">
                      {h.source && `· ${h.source}`} {h.date && `· ${h.date}`}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>

      {/* Праздники */}
      <section>
        <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold muted">
          <CalendarX2 size={14} /> Праздники в даты поездки
        </h4>
        {holidays.length === 0 ? (
          <p className="text-sm muted">
            Национальных праздников на выбранные даты не приходится — толп меньше.
          </p>
        ) : (
          <ul className="space-y-2">
            {holidays.map((h, i) => (
              <li
                key={i}
                className="flex items-start gap-2 rounded-xl border p-3 text-sm"
                style={{ borderColor: "var(--border)" }}
              >
                <AlertTriangle size={16} className="mt-0.5 shrink-0 text-amber-500" />
                <div>
                  <p className="font-semibold">{h.name}</p>
                  <p className="text-xs muted">
                    {fmtDateRu(h.date)} · вероятны толпы и закрытая инфраструктура
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
