#!/usr/bin/env bash
# TRISP — запуск одной командой: ./start.sh
set -euo pipefail
cd "$(dirname "$0")"

UI=http://localhost:3000
API=http://localhost:8000

need_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker не установлен. Установите Docker Desktop: https://www.docker.com/products/docker-desktop/" >&2
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker не запущен — откройте Docker Desktop и повторите." >&2
    exit 1
  fi
}

wait_http() { # url name timeout
  local url=$1 name=$2 t=${3:-120} i=0
  printf "⏳ Ждём %s (%s)… " "$name" "$url"
  while [ $i -lt "$t" ]; do
    if curl -fsS -o /dev/null --max-time 2 "$url"; then echo "OK ✅"; return 0; fi
    sleep 2; i=$((i+2)); printf "."
  done
  echo " ❌ таймаут. Смотрите: ./start.sh logs" >&2
  return 1
}

open_browser() {
  if command -v open >/dev/null 2>&1; then open "$UI"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$UI"
  elif command -v wslview >/dev/null 2>&1; then wslview "$UI"
  else echo "👉 Откройте вручную: $UI"; fi
}

case "${1:-up}" in
  up)
    need_docker
    [ -f .env ] || cp .env.example .env
    docker compose up -d --build
    wait_http "$API/health" "backend" 180
    wait_http "$UI" "frontend" 120
    echo ""
    echo "🌍 UI:    $UI"
    echo "📚 API:   $API/docs"
    echo "❤ Health: $API/health"
    open_browser
    ;;
  status)
    need_docker
    docker compose ps
    curl -fsS "$API/health" && echo " ← backend OK" || echo "backend недоступен"
    curl -fsS -o /dev/null "$UI" && echo "frontend OK ($UI)" || echo "frontend недоступен"
    ;;
  test)
    echo "Smoke-тест POST /api/v1/analyze (Пхукет, ноябрь)…"
    curl -sf -X POST "$API/api/v1/analyze" -H 'Content-Type: application/json' \
      -d '{"place":"Пхукет","date_start":"2026-11-10","date_end":"2026-11-17","trip_type":"beach"}' \
      | python3 -c "import json,sys;d=json.load(sys.stdin);print('score:',d['score']['total'],d['score']['verdict'],'| rain:',d['climate']['rain_risk_pct'],'% | plan_b POIs:',len(d['plan_b']))" \
      || { echo "❌ Проверьте ./start.sh status" >&2; exit 1; }
    ;;
  logs) docker compose logs -f ${2:-} ;;
  restart) need_docker; docker compose restart; wait_http "$UI" "frontend" 60; open_browser ;;
  rebuild) need_docker; docker compose build --no-cache; docker compose up -d; wait_http "$UI" "frontend" 120; open_browser ;;
  down) docker compose down ;;
  local)
    echo "Dev-режим без Docker (нужны Python 3.12+, Node 20+)…"
    ( cd backend && python3 -m venv .venv 2>/dev/null || true; .venv/bin/pip install -q -r requirements.txt; PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8000 & )
    ( cd frontend && npm install --no-audit --no-fund && npm run dev & )
    wait_http "$API/health" "backend" 90
    wait_http "$UI" "frontend(dev)" 120
    open_browser
    echo "Остановка: Ctrl+C / pkill -f uvicorn; pkill -f next"
    wait
    ;;
  *)
    grep '^#' "$0" | head -2
    echo "Команды: up (default) | status | test | logs [сервис] | restart | rebuild | down | local | help"
    ;;
esac
