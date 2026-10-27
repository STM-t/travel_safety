from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения из переменных окружения / .env"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://trisp:trisp_secret@localhost:5432/trisp"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 12 * 60 * 60  # 12 часов

    # LLM (OpenAI-совместимый)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # Внешние API
    http_timeout_seconds: float = 10.0
    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    climate_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    gdelt_doc_url: str = "https://api.gdeltproject.org/api/v2/doc/doc"
    gdacs_rss_url: str = "https://www.gdacs.org/xml/rss.xml"
    nager_holidays_url_template: str = (
        "https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
    )
    overpass_url: str = "https://overpass-api.de/api/interpreter"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://frontend:3000",
        "*",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
