export function fmtTemp(v: number | null | undefined): string {
  if (v == null) return "—";
  const r = Math.round(v * 10) / 10;
  return `${r > 0 ? "+" : ""}${r}°C`;
}

export function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${Math.round(v)}%`;
}

export function fmtNum(v: number | null | undefined, digits = 1): string {
  if (v == null) return "—";
  return v.toFixed(digits);
}

export function fmtDateRu(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export const TRIP_TYPES: { value: "beach" | "tours" | "mountains"; label: string }[] = [
  { value: "beach", label: "Пляж" },
  { value: "tours", label: "Экскурсии" },
  { value: "mountains", label: "Горы/Активный" },
];
