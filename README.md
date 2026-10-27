# TRISP — Trip Risk & Seasonality Intelligence Platform

Анализ климата (10 лет истории), рисков безопасности и сезонности для любой точки мира + AI-вердикт и «План Б» с крытыми местами.

## 🚀 Быстрый старт (2 команды)

```bash
git clone <URL-репозитория> trisp && cd trisp
./start.sh
```

Скрипт сам: проверит Docker → создаст `.env` → соберёт образы → поднимет PostgreSQL, Redis, FastAPI и Next.js → дождётся готовности и откроет браузер.

| Ссылка | Что |
|---|---|
| http://localhost:3000 | 🌍 Дашборд (UI) |
| http://localhost:8000/docs | 📚 Swagger API |
| http://localhost:8000/health | ❤ Health-check |

### Команды start.sh

```bash
./start.sh            # собрать и запустить всё (up)
./start.sh status     # состояние контейнеров + HTTP-проверки
./start.sh test       # smoke-тест /api/v1/analyze через curl
./start.sh logs       # логи (logs backend / logs frontend)
./start.sh restart    # перезапуск
./start.sh rebuild    # пересборка без кэша
./start.sh down       # остановить
./start.sh local      # dev-режим БЕЗ Docker (uvicorn :8000 + next dev :3000)
```

## ✅ Чек-лист проверки UI

1. **Пхукет, 10–17 ноября, тип «Пляж»** → красный вердикт, высокий риск дождя. Первый запрос 30–90 сек.
2. Графики дождливых дней по годам + бейджи метрик.
3. «Радар рисков»: алерты GDACS и лента GDELT (при недоступности — честная плашка деградации).
4. AI-вердикт: бейдж «Правила» без LLM_API_KEY, «LLM» — с ключом из `.env`.
5. «План Б»: карточки музеев/кинотеатров + интерактивная карта OSM.
6. Контрастный тест: **Канкун, 10–17 марта** → высокий зелёный score.
7. Переключение тёмной/светлой темы.

## 🔧 Ручной запуск без скрипта

```bash
cp .env.example .env
docker compose up -d --build
```

## 🧪 Тест API

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H 'Content-Type: application/json' \
  -d '{"place":"Пхукет","date_start":"2026-11-10","date_end":"2026-11-17","trip_type":"beach"}'
```

## ⚠ Возможные проблемы

| Симптом | Решение |
|---|---|
| «Docker не запущен» | Откройте Docker Desktop, подождите, повторите `./start.sh` |
| Порт 3000/8000 занят | `lsof -i :3000`, завершите процесс или поменяйте port в docker-compose.yml |
| Долгая первая сборка | Нормально (~3–7 мин: npm install + pip install) |
| postgres не healthy | `docker compose down -v && ./start.sh` |
| GDELT/GDACS недоступны | UI покажет деградацию — остальные блоки работают |

## Архитектура

```
backend/   FastAPI + httpx: Open-Meteo (геокодер, климат-история, прогноз), GDELT, GDACS,
           Nager.Date, Overpass; scoring (Climate/Safety/Seasonality, веса по типу поездки);
           AI-synthesis (OpenAI-совместимый LLM + rule-based fallback)
frontend/  Next.js 14 App Router + TypeScript + Tailwind + recharts:
           ScoreGauge, ClimateBlock, RiskFeed, AiVerdict, PlanB (карта OSM), темы, skeleton
infra/     docker-compose.yml: postgres + redis + backend(:8000) + frontend(:3000)
```

LLM: `.env` → `LLM_API_KEY`, `LLM_BASE_URL` (любой OpenAI-совместимый), `LLM_MODEL`. Без ключа — детерминированный rule-based вердикт.
