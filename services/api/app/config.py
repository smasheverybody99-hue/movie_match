"""Application settings. The only place environment variables are read."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# services/api/.env, wherever the process was started from.
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    env: str = "development"

    database_url: str = ""
    # Throwaway database for DB-backed tests and the migration round-trip. Only tests
    # read it; the Alembic CLI always targets database_url. Never point it at real data.
    test_database_url: str = ""
    supabase_jwt_secret: str = ""

    tmdb_api_key: str = ""
    # Which provider does traits, embeddings and explanations: a key of
    # app.providers.PROVIDERS. The choice is open (ADR 0006); "gemini" is what exists.
    llm_provider: str = "gemini"
    # Size of movie_embeddings.embedding. Must equal the column in the database: the API
    # and the embeddings pipeline check it on start and refuse to run on a mismatch.
    # Changing it means a migration and re-embedding every film (ADR 0006).
    embedding_dim: int = Field(default=1536, ge=1)
    # The API's start-up schema check (embedding size). Tests switch it off so that
    # importing the app never connects to DATABASE_URL.
    schema_check_on_startup: bool = True
    # Gemini (ADR 0004). Paid tier: the free tier lets Google use submitted content to
    # train its models.
    gemini_api_key: str = ""
    # Not used by the data pipelines; the Phase 4 assistant still runs on Claude.
    anthropic_api_key: str = ""
    redis_url: str = ""

    cors_origins: str = "http://localhost:5173"

    # Catalogue. The target is deliberately a setting: raise it here, not in code.
    # 500 since 2026-09-30, for cost: trait and embedding spend grow with the film count
    # (docs/costs.md, TZ FR-2). The database may hold more films than this.
    catalogue_target: int = 500
    # Floor on TMDB vote count, so "popular" means known rather than briefly trending.
    catalogue_min_votes: int = 100
    # No single original language may fill more than this share of a decade's quota
    # while other languages still have candidates.
    catalogue_max_language_share: float = 0.55

    # TMDB politeness. Their documented ceiling is ~50 req/s per IP; stay well under it.
    tmdb_requests_per_second: float = 20.0
    tmdb_concurrency: int = 8

    # Cost guards. Raise deliberately, never silently.
    assistant_daily_calls_per_user: int = 30
    # "Why you'll like this" generations per user per day. Cached ones are free and
    # unlimited. 20 a day at ~$0.0003 each keeps even a daily heavy user near TZ's
    # $0.20 a month.
    explanation_daily_calls_per_user: int = 20
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
