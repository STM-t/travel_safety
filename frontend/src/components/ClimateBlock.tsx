"use client";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { CloudRain, ThermometerSun, Wind, Waves } from "lucide-react";
import type { ClimateOut } from "@/lib/types";
import { fmtPct, fmtTemp, fmtNum } from "@/lib/format";

interface Props {
  climate: ClimateOut;
}

export default function ClimateBlock({ climate }: Props) {
  const series = (climate.yearly_series ?? [])
    .slice()
    .sort((a, b) => a.year - b.year)
    .map((p) => ({
      year: String(p.year),
      rain_days_pct: p.rain_days_pct != null ? Math.round(p.rain_days_pct) : null,
      avg_temp_max: p.avg_temp_max != null ? Math.round(p.avg_temp_max * 10) / 10 : null,
      avg_temp_min: p.avg_temp_min != null ? Math.round(p.avg_temp_min * 10) / 10 : null,
    }));

  const badges = [
    {
      icon: CloudRain,
      label: "Риск дождя",
      value: fmtPct(climate.rain_day_probability),
      hint: "дни с осадками > 3 мм",
      danger: (climate.rain_day_probability ?? 0) > 20,
    },
    {
      icon: Waves,
      label: "Ливни > 15 мм",
      value: fmtPct(climate.heavy_rain_risk),
      hint: "риск тропических ливней",
      danger: (climate.heavy_rain_risk ?? 0) > 8,
    },
    {
      icon: ThermometerSun,
      label: "Средний максимум",
      value: fmtTemp(climate.avg_temp_max),
      hint: `минимум ${fmtTemp(climate.avg_temp_min)}`,
      danger: false,
    },
    {
      icon: Wind,
      label: "Штормовой ветер",
      value: fmtPct(climate.storm_wind_risk),
      hint: "порывы > 40 км/ч",
      danger: (climate.storm_wind_risk ?? 0) > 5,
    },
  ];

  return (
    <div className="card">
      <h3 className="mb-1 flex items-center gap-2 text-lg font-bold">
        <CloudRain size={18} className="text-sky-500" /> Климат за те же даты за 10 лет
      </h3>
      <p className="mb-4 text-xs muted">
        Исторические данные Open-Meteo Archive API,{" "}
        {climate.total_days_sampled} дней выборки
      </p>

      {climate.error && (
        <p className="mb-3 rounded-lg bg-amber-500/10 px-3 py-2 text-sm text-amber-600">
          Данные климата частично недоступны: {climate.error}
        </p>
      )}

      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {badges.map((b) => (
          <div
            key={b.label}
            className="rounded-xl border p-3"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="mb-1 flex items-center gap-1.5 text-xs muted">
              <b.icon size={14} /> {b.label}
            </div>
            <div
              className={`text-xl font-bold tabular-nums ${
                b.danger ? "text-red-500" : ""
              }`}
            >
              {b.value}
            </div>
            <div className="text-[11px] muted">{b.hint}</div>
          </div>
        ))}
      </div>

      {series.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div>
            <h4 className="mb-2 text-sm font-semibold muted">
              Дождливые дни по годам, %
            </h4>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={series}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="var(--muted)" />
                <YAxis unit="%" tick={{ fontSize: 11 }} stroke="var(--muted)" />
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(v: number) => [`${v}%`, "Дождливые дни"]}
                />
                <Bar dataKey="rain_days_pct" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div>
            <h4 className="mb-2 text-sm font-semibold muted">
              Температуры по годам, °C
            </h4>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={series}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="var(--muted)" />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--muted)" />
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(v: number) => [`${v}°C`]}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line
                  type="monotone"
                  dataKey="avg_temp_max"
                  name="Дневной максимум"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="avg_temp_min"
                  name="Ночной минимум"
                  stroke="#818cf8"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <p className="text-sm muted">Нет данных для графика.</p>
      )}

      {climate.avg_radiation_mj != null && (
        <p className="mt-3 text-xs muted">
          Средняя солнечная радиация: {fmtNum(climate.avg_radiation_mj)} МДж/м² в сутки ·
          Пиковый максимум: {fmtTemp(climate.max_temp_peak)} · Пиковый минимум:{" "}
          {fmtTemp(climate.min_temp_peak)}
        </p>
      )}
    </div>
  );
}
