"""Redis-кэш ответов (TTL 12 часов) + PostgreSQL (история поисков, метаданные локаций).

Всё работает в режиме graceful degradation: если Redis/Postgres недоступны,
анализ продолжается без кэша и персистентности.
"""
from __future__ import annotations

import hashlib
import json
import logging

import redis.asyncio as aioredis
from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..config import get_settings

logger = logging.getLogger("trisp.cache")


class Base(DeclarativeBase):
    pass


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    destination = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    trip_type = Column(String(30), nullable=False)
    score_total = Column(Float, nullable=True)
    verdict = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CachedLocation(Base):
    __tablename__ = "cached_locations"

    query = Column(String(200), primary_key=True)
    name = Column(String(200))
    lat = Column(Float)
    lon = Column(Float)
    country_code = Column(String(8))
    country = Column(String(100))
    admin1 = Column(String(200))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Infra:
    """Singleton-обёртка над Redis и SQLAlchemy."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis: aioredis.Redis | None = None
        self.engine = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    async def init(self) -> None:
        try:
            self.redis = aioredis.from_url(
                self.settings.redis_url, decode_responses=True,
                socket_connect_timeout=3, socket_timeout=3,
            )
            await self.redis.ping()
            logger.info("Redis connected")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis unavailable: %s", exc)
            # Локальная разработка без docker-compose: in-memory совместимый кэш
            try:
                import fakeredis.aioredis

                self.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
                await self.redis.ping()
                logger.info("Using in-process fakeredis fallback cache")
            except Exception:  # noqa: BLE001
                self.redis = None

        try:
            self.engine = create_async_engine(
                self.settings.database_url, pool_size=5, max_overflow=5,
                connect_args={"timeout": 5},
            )
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
            logger.info("PostgreSQL connected")
        except Exception as exc:  # noqa: BLE001
            logger.warning("PostgreSQL unavailable: %s — falling back to SQLite", exc)
            if self.engine:
                try:
                    await self.engine.dispose()
                except Exception:  # noqa: BLE001
                    pass
            try:
                import os

                db_path = os.path.join(os.getcwd(), "trisp_local.db")
                self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
                logger.info("SQLite fallback connected (dev only)")
            except Exception as exc2:  # noqa: BLE001
                logger.warning("SQLite fallback unavailable: %s", exc2)
                self.engine = None
                self.session_factory = None

    async def close(self) -> None:
        if self.redis:
            await self.redis.aclose()
        if self.engine:
            await self.engine.dispose()

    # ---- Redis report cache ----
    @staticmethod
    def report_key(destination: str, start: str, end: str, trip_type: str) -> str:
        raw = f"{destination.lower().strip()}|{start}|{end}|{trip_type}"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:24]
        return f"trisp:report:{digest}"

    async def cache_get(self, key: str) -> dict | None:
        if not self.redis:
            return None
        try:
            val = await self.redis.get(key)
            return json.loads(val) if val else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_get failed: %s", exc)
            return None

    async def cache_set(self, key: str, value: dict) -> None:
        if not self.redis:
            return
        try:
            await self.redis.set(key, json.dumps(value, ensure_ascii=False),
                                 ex=self.settings.cache_ttl_seconds)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_set failed: %s", exc)

    # ---- Postgres helpers ----
    async def save_search(self, destination: str, start, end, trip_type: str,
                          score_total: float | None, verdict: str | None) -> None:
        if not self.session_factory:
            return
        try:
            async with self.session_factory() as s:
                s.add(SearchHistory(
                    destination=destination, start_date=start, end_date=end,
                    trip_type=trip_type, score_total=score_total, verdict=verdict,
                ))
                await s.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("save_search failed: %s", exc)

    async def get_location_meta(self, query: str) -> dict | None:
        if not self.session_factory:
            return None
        try:
            async with self.session_factory() as s:
                row = await s.get(CachedLocation, query.lower().strip())
                if row:
                    return {
                        "name": row.name, "lat": row.lat, "lon": row.lon,
                        "country_code": row.country_code, "country": row.country,
                        "admin1": row.admin1,
                    }
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_location_meta failed: %s", exc)
        return None

    async def save_location_meta(self, query: str, loc: dict) -> None:
        if not self.session_factory:
            return
        try:
            async with self.session_factory() as s:
                existing = await s.get(CachedLocation, query.lower().strip())
                if existing:
                    return
                s.add(CachedLocation(query=query.lower().strip(), **loc))
                await s.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("save_location_meta failed: %s", exc)

    async def redis_ok(self) -> bool:
        if not self.redis:
            return False
        try:
            return await self.redis.ping()
        except Exception:  # noqa: BLE001
            return False

    async def postgres_ok(self) -> bool:
        if not self.engine:
            return False
        try:
            async with self.engine.connect() as conn:
                await conn.execute(select(1))
            return True
        except Exception:  # noqa: BLE001
            return False


infra = Infra()
