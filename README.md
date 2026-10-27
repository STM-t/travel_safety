# TRISP — Travel Risk & Seasonality Intelligence Platform

**Умный радар рисков и сезонности для путешественников.** В отличие от агрегаторов
бронирования, сервис выступает «адвокатом путешественника»: вводит город/курорт и даты —
платформа агрегирует 10-летнюю климатическую статистику, геополитические риски, алерты
стихийных бедствий, праздники и выдаёт честный AI-вердикт + крытый «План Б» на случай дождя.

## Архитектура

```
├── docker-compose.yml      # postgres 16 + redis 7 + backend + frontend
├── .env.example            # конфигурация (БД, кэш, LLM, фронтенд)
├── backend/                # Python 3.12 + FastAPI (async), httpx, asyncio.gather
│   └── app/
│       ├── adapters/       # geocoding, climate, gdelt, gdacs, holidays, overpass
│       ├── services/       # orchestrator, scoring_engine (scoring.py), ai.py, storage.py
│       ├── api/analyze.py  # POST /api/v1/analyze
│       ├── schemas.py      # Pydantic-схемы запроса/ответа
│       └── main.py         # CORS, health-check, запуск
└── frontend/               # Next.js 14 (App Router) + TypeScript + Tailwind CSS
    └── src/
        ├── app/            # layout (dark/light), page (дашборд)
        ├── components/     # SearchBar, ScoreGauge, ClimateBlock (recharts),
        │                   # RiskFeed, AiVerdict, PlanB (карта OSM), Skeleton…
        └── lib/            # api.ts, types.ts, format.ts
```

## Внешние источники (без ключей, реальные данные)

| Источник | Что даёт |
|---|---|
| Open-Meteo Geocoding | координаты города, страна |
| Open-Meteo Historical Archive | daily t_max/t_min/осадки/ветер/радиация за те же даты × 10 лет |
| GDELT DOC 2.0 | протесты/забастовки/беспорядки за 30 дней, тон, топ-5 заголовков |
| GDACS RSS | активные бедствия (циклоны, землетрясения, наводнения) в радиусе 500 км |
| Nager.Date | национальные праздники в даты поездки |
| Overpass (OSM) | крытые POI (музеи, ТРЦ, спа…) в радиусе 15 км — при риске дождя > 20% |

Все адаптеры имеют таймаут 10 с и graceful degradation: отказ одного API не роняет
отчёт — источник помечается в `degraded_sources`.

## Запуск (одной командой)

```bash
cp .env.example .env          # при желании заполните LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
docker compose up --build
```

* Фронтенд: **http://localhost:3000** (интерфейс на русском, тёмная/светлая тема)
* Backend API: **http://localhost:8000/docs** (Swagger)
* Health: `curl http://localhost:8000/api/v1/health`

Без Docker (локальная разработка):

```bash
# backend (нужны PostgreSQL и Redis, либо оставьте DATABASE_URL/REDIS_URL на localhost)
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && npm install && NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## Тестирование API

```bash
curl -s -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"destination":"Phuket","start_date":"2026-11-10","end_date":"2026-11-20","trip_type":"beach"}'
```

Ответ содержит: `location`, `score` (0–100 + breakdown), `climate` (10-летняя серия),
`geopolitics`, `disasters`, `holidays`, `plan_b`, `ai_verdict_md`, `degraded_sources`.

## Математика скоринга

`Score = 0.45·S_климат + 0.35·S_безопасность + 0.20·S_сезонность`

* **S_климат:** −1.2 балла за каждый 1% вероятности дождя, штрафы за ливни >15 мм,
  жару >36 °C, холод <12 °C (для пляжа пороги строже), штормовой ветер >40 км/ч.
* **S_безопасность:** штрафы за объём новостей GDELT о протестах/забастовках и
  Red/Orange-алерты GDACS в радиусе 500 км.
* **S_сезонность:** штрафы за пересечение с национальными праздниками (толпы).

Светофор: **80–100 зелёный** («Отличное время»), **50–79 жёлтый** («Есть скрытые риски:
нужен План Б»), **0–49 красный** («Высокий риск испорченного отпуска»).

## AI-синтез и guardrails

`services/ai.py` передаёт в LLM строго JSON метрик с системным промптом:
«никогда не выдумывай цифры погоды и политические события». Если `LLM_API_KEY` пуст —
включается детерминированный rule-based fallback на русском (TL;DR, красные флаги,
совет по датам, План Б), поэтому MVP работает без ключей (`ai_source: "fallback"`).

## Кэширование

Redis: полный отчёт по ключу `(destination, dates, trip_type)` с TTL 12 часов
(`CACHE_TTL_SECONDS`). Повторные запросы помечаются `cached: true`.
PostgreSQL хранит историю поисков и метаданные локаций.
