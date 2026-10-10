"""Application settings. The only place environment variables are read."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

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
    # The Supabase project, e.g. https://abcd.supabase.co (the web's VITE_SUPABASE_URL).
    # Access tokens are verified against its public signing keys, `<url>/auth/v1/.well-known
    # /jwks.json`, and its issuer `<url>/auth/v1` (ADR 0007).
    supabase_project_url: str = ""
    # Legacy HS256 shared secret. Leave empty: the project signs with asymmetric keys now,
    # and while this is set, HS256 tokens made with it are accepted (ADR 0007).
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
    # The commit Render deployed: Render sets RENDER_GIT_COMMIT on every deploy. /health
    # reports it, so each push can be checked against what is live (docs/deploy.md, 1b).
    # Empty when run locally.
    render_git_commit: str = ""

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
    # unlimited. Measured 2026-10-02: ~$0.00013 each at the standard rate, so 20 a day is
    # ~$0.08 a month for the heaviest user, inside TZ's $0.20 (docs/costs.md).
    explanation_daily_calls_per_user: int = 20
    # Which traits are named as the reasons for a match (matching.top_reasons). In
    # catalogue standard deviations: the film must stand out by at least this much...
    reason_min_film_z: float = 0.5
    # ...and the user's taste must sit at least this far on the same side of the mean.
    reason_min_taste_z: float = 0.0
    # Match bands (FR-5, TZ 1.13): the client shows these, not the number. Places are the
    # film's rank among every film with traits, for this user. "strong": one of the N
    # closest (an absolute count, so the red badges on Home stay few as the catalogue
    # grows; 5 gave 2-3 on one account's first screen, 2026-10-05).
    match_strong_top_n: int = Field(default=5, ge=1)
    # "good": within this closest share of the catalogue. 0.35 put a band on every third
    # film page (175 of 500), too often to mean much; 0.15 since 2026-10-05.
    match_good_share: float = Field(default=0.15, gt=0, le=1)
    # Never recommended: this furthest share of the catalogue (replaced the 60% cut,
    # which removed 2 of 473 films).
    match_floor_share: float = Field(default=0.25, ge=0, lt=1)
    trait_batch_size: int = 200
    # How trait extraction runs (ADR 0006, amendment 2026-09-30). "batch": the provider's
    # batch API, half price, needs an account that allows it. "sync": one film per request
    # on the standard API; slower, full price on a paid tier, works on Gemini's free tier.
    trait_mode: Literal["batch", "sync"] = "batch"
    # sync mode: requests per minute. Free-tier limits are per model and per project and
    # change; 10 is deliberately below them. A 429 is waited out and retried
    # `trait_sync_retries` times per film, then the run stops and can be resumed.
    trait_sync_requests_per_minute: float = Field(default=10, gt=0)
    trait_sync_retries: int = Field(default=5, ge=0)
    # Embedding runs: one film per request, paced like sync traits (ADR 0006). The free
    # tier's embedding limits are per model and change; 20 a minute is below them.
    embedding_requests_per_minute: float = Field(default=20, gt=0)
    embedding_retries: int = Field(default=5, ge=0)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
