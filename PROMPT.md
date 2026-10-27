# Role & Objective
Act as a Principal Full-Stack Engineer and System Architect. Your task is to build a working, production-ready MVP of the **"Travel Risk & Seasonality Intelligence Platform"** (Умный радар рисков и сезонности для путешественников). 

Unlike booking aggregators that try to sell trips at all costs, this service acts as a "traveler's advocate." The user inputs a **Destination** (city/resort) and **Dates** (`start_date`, `end_date`), and the platform aggregates 10-year historical climate statistics, geopolitical/protest risks, natural disaster alerts, public holidays, and generates an AI-powered verdict along with an indoor **"Plan B"** in case of bad weather.

---

# 1. Tech Stack & Architecture (Modular Monolith MVP)
Build a clean, modular architecture that runs locally with a single `docker compose up --build` command:
* **Backend:** Python 3.12 + **FastAPI** (async). Use `httpx` for concurrent external API calls (`asyncio.gather`).
* **Database & Cache:** **PostgreSQL 16** (search history, cached location metadata) + **Redis 7** (caching API responses and calculated scores with a 12-hour TTL).
* **Frontend:** **Next.js 14+ (App Router)**, TypeScript, Tailwind CSS, `lucide-react` icons, and `recharts` for climate visualization. (Alternatively, keep the frontend tightly coupled via clean REST API).
* **AI Integration:** OpenAI-compatible SDK (`AsyncOpenAI`) configurable via `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` in `.env` (must include a deterministic rule-based fallback if no API key is provided so the MVP never crashes).
* **Language:** All UI elements, risk badges, and AI summaries MUST be in **Russian**.

---

# 2. Zero-Auth External Data Providers (Real Integrations Only — No Mock Data!)
Implement clean `Adapter` classes with timeouts (10s) and graceful degradation (if one API fails, return partial data without crashing):

1. **Geocoding:** `Open-Meteo Geocoding API` (`https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru`) -> Extracts `lat`, `lon`, `country_code`, `name`.
2. **Historical Climate Engine:** `Open-Meteo Historical Archive API` (`https://archive-api.open-meteo.com/v1/archive`).
   * Fetch daily data for the requested `start_date` to `end_date` window across the **last 10 years**.
   * Parameters: `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `wind_speed_10m_max`, `shortwave_radiation_sum`.
   * Calculate: 
     * `rain_day_probability` (% of days with `precipitation_sum > 3.0 mm`).
     * `heavy_rain_risk` (% of days with `precipitation_sum > 15.0 mm`).
     * `avg_temp_max`, `avg_temp_min`, `storm_wind_risk` (`wind_speed_10m_max > 40 km/h`).
3. **Geopolitics, Protests & Strikes:** `GDELT DOC 2.0 API` (`https://api.gdeltproject.org/api/v2/doc/doc`)
   * Query recent news (last 30 days) for the destination city/country with keywords: `(protest OR strike OR unrest OR riot OR evacuation OR flood)`.
   * Return article count, tone/sentiment indicator, and top 5 recent headlines with URLs.
4. **Natural Disasters & Bio/Eco Alerts:** `GDACS API` (Global Disaster Alert and Coordination System RSS/GeoJSON feed `https://www.gdacs.org/xml/rss.xml`)
   * Check for active cyclones, earthquakes, floods, or wildfires within a 500 km radius of (`lat`, `lon`).
5. **Seasonality & Local Holidays:** `Nager.Date API` (`https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}`)
   * Detect if the user's travel dates overlap with national/religious holidays (crowds, closed infrastructure).
6. **"Plan B" Indoor Places Generator:** `OpenStreetMap Overpass API` (`https://overpass-api.de/api/interpreter`)
   * Triggered automatically if `rain_day_probability > 20%` (or on demand).
   * Query within 15 km of (`lat`, `lon`) for top indoor POIs: `tourism=museum`, `tourism=aquarium`, `tourism=gallery`, `shop=mall`, `leisure=spa`, `leisure=sports_centre`. Return top 6 places with names, categories, and map coordinates.

---

# 3. Mathematical Scoring Engine (`Trip Viability Score` 0–100)
Create a dedicated `scoring_engine.py` module that computes a weighted score:
$$Score = 0.45 \times S_{climate} + 0.35 \times S_{safety} + 0.20 \times S_{seasonality}$$

* **$S_{climate}$ (0–100):** Starts at 100. Penalize for high `rain_day_probability` (e.g., `-1.2` points per 1% chance of rain), heavy rain spikes, extreme heat (`>36°C`) or cold (`<12°C` for beach/general leisure), and strong winds.
* **$S_{safety}$ (0–100):** Starts at 100. Penalize based on GDELT protest/strike volume and active GDACS Red/Orange disaster alerts within radius.
* **$S_{seasonality}$ (0–100):** Starts at 100. Penalize for major public holiday overlaps (crowd risk) and shoulder-season weather instability.
* **Traffic Light Verdict:**
  * `80–100`: **Green** («Отличное время для поездки»)
  * `50–79`: **Yellow** («Есть скрытые риски: нужен План Б»)
  * `0–49`: **Red** («Высокий риск испорченного отпуска»)

---

# 4. AI Synthesis & Guardrails (RAG Approach)
Create an `ai_synthesizer.py` service that feeds the strict JSON output from the adapters and `scoring_engine.py` into the LLM.
* **Strict System Prompt:** The LLM must NEVER invent weather numbers or political events. It must rely strictly on the provided JSON metrics.
* **Output Structure (in Russian):**
  1. **Главный вердикт (TL;DR):** 2–3 sentences explaining the score honestly.
  2. **Красные флаги (Red Flags):** Bullet points of specific threats (e.g., "Исторически 35% дней в этот период идут тропические ливни", "В регионе зафиксированы забастовки транспорта").
  3. **Совет по датам / альтернативам:** Advice on shifting dates or preparing specific gear.
  4. **Чем заняться в дождь (План Б):** Brief narrative linking to the fetched Overpass indoor locations.

---

# 5. API Endpoints & Frontend Dashboard
### Backend Endpoints:
* `POST /api/v1/analyze` — Accepts `{"destination": "Phuket", "start_date": "2026-11-10", "end_date": "2026-11-20", "trip_type": "beach"}`. Orchestrates all adapters in parallel, caches in Redis, and returns the unified JSON report.
* `GET /api/v1/health` — Returns status of DB, Redis, and external API reachability.

### Frontend UI (Russian Interface):
Build a modern, dark/light responsive dashboard:
1. **Search Bar:** City/Resort input, Date Range picker, Trip Type selector (`Пляж`, `Экскурсии`, `Горы/Активный`).
2. **Hero Gauge Card:** Big `Trip Viability Score (0-100)` with Traffic Light color coding + breakdown progress bars (`Климат`, `Безопасность`, `Сезонность`).
3. **Climate Analytics Block:** Bar/Line chart showing the last 10 years of rainfall and temperature for those exact dates + clear metric badges (`Риск дождя: X%`, `Средний максимум: +Y°C`, `Риск штормового ветра`).
4. **Geopolitics & Alerts Feed:** List of detected protests, strikes, or natural hazards with source links and holiday warnings.
5. **AI Verdict & Interactive "Plan B" Block:** Rendered markdown summary from LLM + cards of real indoor venues (Museums, Malls, Spas) on the resort map to save the vacation if it rains.

---

# 6. Execution Instructions for the Agent
1. First, generate the project directory tree and `docker-compose.yml` + `.env.example`.
2. Implement the backend modularly (`app/adapters/`, `app/services/scoring.py`, `app/services/ai.py`, `app/api/`, `app/schemas.py`).
3. Implement the frontend dashboard with clean loading states (skeleton loaders while historical APIs aggregate data).
4. Write a comprehensive `README.md` with launch and testing instructions.
5. Write complete, working code without `TODO` placeholders. Begin implementation now.
