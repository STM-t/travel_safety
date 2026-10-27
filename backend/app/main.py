import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.base import make_client
from .api.analyze import router as analyze_router
from .config import get_settings
from .services.storage import infra

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("trisp.main")

app = FastAPI(
    title="Travel Risk & Seasonality Intelligence Platform",
    description="Умный радар рисков и сезонности для путешественников (MVP)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.on_event("startup")
async def startup() -> None:
    await infra.init()


@app.on_event("shutdown")
async def shutdown() -> None:
    await infra.close()


EXTERNAL_CHECKS = {
    "open_meteo_geocoding": "https://geocoding-api.open-meteo.com/v1/search?name=Rome&count=1",
    "open_meteo_archive": "https://archive-api.open-meteo.com/v1/archive?latitude=41&longitude=12&start_date=2024-01-01&end_date=2024-01-02&daily=temperature_2m_max",
    "gdelt": "https://api.gdeltproject.org/api/v2/doc/doc?query=rome&mode=ArtList&maxrecords=1&format=json",
    "gdacs": "https://www.gdacs.org/xml/rss.xml",
    "nager_date": "https://date.nager.at/api/v3/PublicHolidays/2026/IT",
    "overpass": "https://overpass-api.de/api/status",
}


@app.get("/api/v1/health")
async def health():
    """Статус БД, Redis и доступности внешних API."""
    async with make_client() as client:
        # быстрая проверка reachability HEAD/GET с коротким таймаутом
        import asyncio

        async def check(name: str, url: str) -> bool:
            try:
                r = await client.get(url)
                return r.status_code < 500
            except Exception:  # noqa: BLE001
                return False

        api_results = await asyncio.gather(
            *(check(n, u) for n, u in EXTERNAL_CHECKS.items())
        )
    external = dict(zip(EXTERNAL_CHECKS.keys(), api_results))

    redis_ok = await infra.redis_ok()
    pg_ok = await infra.postgres_ok()

    status = "ok" if (redis_ok and pg_ok and all(external.values())) else "degraded"
    return {
        "status": status,
        "postgres": "up" if pg_ok else "down",
        "redis": "up" if redis_ok else "down",
        "external_apis": external,
        "llm_configured": bool(get_settings().llm_api_key),
    }


@app.get("/")
async def root():
    return {"service": "Travel Risk & Seasonality Intelligence Platform",
            "docs": "/docs", "health": "/api/v1/health"}
