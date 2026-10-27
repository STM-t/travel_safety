"use client";

import { useState } from "react";
import { Umbrella, MapPin, Landmark, ShoppingBag, Dumbbell, Flower2, Image, ExternalLink } from "lucide-react";
import type { PlaceOut, LocationOut } from "@/lib/types";

interface Props {
  places: PlaceOut[];
  location: LocationOut;
  triggeredByRain: boolean;
}

const CAT_ICONS: Record<string, React.ReactNode> = {
  museum: <Landmark size={16} className="text-indigo-500" />,
  aquarium: <Umbrella size={16} className="text-sky-500" />,
  gallery: <Image size={16} className="text-purple-500" />,
  mall: <ShoppingBag size={16} className="text-pink-500" />,
  spa: <Flower2 size={16} className="text-emerald-500" />,
  sports_centre: <Dumbbell size={16} className="text-orange-500" />,
};

export default function PlanB({ places, location, triggeredByRain }: Props) {
  const [active, setActive] = useState<number | null>(null);

  if (places.length === 0) {
    return (
      <div className="card">
        <h3 className="mb-2 flex items-center gap-2 text-lg font-bold">
          <Umbrella size={18} className="text-sky-500" /> План Б — куда спрятаться от дождя
        </h3>
        <p className="text-sm muted">
          Риск дождя низкий — крытые площадки не запрашивались. Но на всякий случай
          держите в запасе пару музеев из открытых источников.
        </p>
      </div>
    );
  }

  const selected = active != null ? places[active] : null;
  const center = selected ?? { lat: location.lat, lon: location.lon };
  const zoom = selected ? 14 : 11;
  const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${center.lon - 0.05}&layer=mapnik&marker=${center.lat},${center.lon}`;

  return (
    <div className="card">
      <h3 className="mb-1 flex items-center gap-2 text-lg font-bold">
        <Umbrella size={18} className="text-sky-500" /> План Б — крытые места рядом
      </h3>
      <p className="mb-4 text-xs muted">
        Реальные точки с OpenStreetMap (Overpass API) в радиусе 15 км ·{" "}
        {triggeredByRain
          ? "показаны, потому что риск дождя выше 20%"
          : "запрошены по требованию"}
      </p>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ul className="space-y-2">
          {places.map((p, i) => (
            <li key={i}>
              <button
                onClick={() => setActive(i)}
                className={`w-full rounded-xl border p-3 text-left transition hover:border-indigo-500 ${
                  active === i ? "border-indigo-500 ring-1 ring-indigo-500/40" : ""
                }`}
                style={{ borderColor: active === i ? undefined : "var(--border)" }}
              >
                <div className="flex items-center gap-2">
                  {CAT_ICONS[p.category] ?? <MapPin size={16} />}
                  <span className="min-w-0 flex-1 truncate text-sm font-semibold">
                    {p.name || "Без названия"}
                  </span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs muted">
                  <span>{p.category_ru}</span>
                  <span>
                    {p.distance_km != null ? `~${Math.round(p.distance_km)} км` : ""}
                  </span>
                </div>
              </button>
            </li>
          ))}
        </ul>

        <div className="overflow-hidden rounded-xl border" style={{ borderColor: "var(--border)" }}>
          <iframe
            title="Карта План Б"
            src={mapUrl}
            className="h-[320px] w-full lg:h-full"
            loading="lazy"
          />
        </div>
      </div>

      {selected && (
        <div className="mt-3 text-xs muted">
          Выбрано: <b>{selected.name}</b> ·{" "}
          <a
            className="inline-flex items-center gap-1 text-indigo-500 hover:underline"
            target="_blank"
            rel="noreferrer"
            href={`https://www.openstreetmap.org/?mlat=${selected.lat}&mlon=${selected.lon}#map=15/${selected.lat}/${selected.lon}`}
          >
            Открыть в OSM <ExternalLink size={11} />
          </a>
        </div>
      )}
    </div>
  );
}
