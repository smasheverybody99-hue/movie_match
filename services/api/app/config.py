"""Application settings. The only place environment variables are read."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    database_url: str = ""
    # Throwaway database for DB-backed tests and the migration round-trip. When set,
    # Alembic targets it instead of database_url. Never point it at real data.
    test_database_url: str = ""
    supabase_jwt_secret: str = ""

    tmdb_api_key: str = ""
    anthropic_api_key: str = ""
    redis_url: str = ""

    cors_origins: str = "http://localhost:5173"

    # Cost guards. Raise deliberately, never silently.
    assistant_daily_calls_per_user: int = 30
    trait_batch_size: int = 200

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
