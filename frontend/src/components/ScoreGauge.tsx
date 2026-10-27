"use client";

import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import type { ScoreOut } from "@/lib/types";

const COLORS = {
  green: "#22c55e",
  yellow: "#eab308",
  red: "#ef4444",
};

const VERDICT_ICONS = {
  green: CheckCircle2,
  yellow: AlertTriangle,
  red: XCircle,
};

interface Props {
  score: ScoreOut;
  locationName: string;
  country: string;
  cached: boolean;
}

export default function ScoreGauge({ score, locationName, country, cached }: Props) {
  const color = COLORS[score.verdict] ?? COLORS.yellow;
  const Icon = VERDICT_ICONS[score.verdict] ?? AlertTriangle;

  const total = Math.max(0, Math.min(100, score.total));
  const r = 68;
  const circ = 2 * Math.PI * r;
  const dash = (total / 100) * circ;

  const bars: { label: string; value: number; weight: string }[] = [
    { label: "Климат", value: score.climate, weight: "45%" },
    { label: "Безопасность", value: score.safety, weight: "35%" },
    { label: "Сезонность", value: score.seasonality, weight: "20%" },
  ];

  function barColor(v: number) {
    if (v >= 80) return COLORS.green;
    if (v >= 50) return COLORS.yellow;
    return COLORS.red;
  }

  return (
    <div className="card flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">{locationName}</h2>
          <p className="text-sm muted">{country}</p>
        </div>
        {cached && (
          <span className="rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-500">
            Из кэша
          </span>
        )}
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        {/* Круговой индикатор */}
        <div className="relative shrink-0" style={{ width: 168, height: 168 }}>
          <svg width={168} height={168} viewBox="0 0 168 168">
            <circle
              cx={84}
              cy={84}
              r={r}
              fill="none"
              stroke="var(--border)"
              strokeWidth={12}
            />
            <circle
              cx={84}
              cy={84}
              r={r}
              fill="none"
              stroke={color}
              strokeWidth={12}
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circ}`}
              transform="rotate(-90 84 84)"
              style={{ transition: "stroke-dasharray 0.8s ease" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-extrabold tabular-nums">
              {Math.round(total)}
            </span>
            <span className="text-xs muted">из 100</span>
          </div>
        </div>

        {/* Вердикт */}
        <div className="flex-1">
          <div
            className="mb-3 inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold"
            style={{ background: `${color}22`, color }}
          >
            <Icon size={18} />
            {score.verdict_ru}
          </div>
          <div className="space-y-3">
            {bars.map((b) => (
              <div key={b.label}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="muted">
                    {b.label} <span className="opacity-60">(вес {b.weight})</span>
                  </span>
                  <span className="font-semibold tabular-nums">
                    {Math.round(b.value)}
                  </span>
                </div>
                <div
                  className="h-2 w-full overflow-hidden rounded-full"
                  style={{ background: "var(--border)" }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.max(0, Math.min(100, b.value))}%`,
                      background: barColor(b.value),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {score.notes.length > 0 && (
        <ul className="space-y-1 border-t pt-3 text-xs muted" style={{ borderColor: "var(--border)" }}>
          {score.notes.map((n, i) => (
            <li key={i}>• {n}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
