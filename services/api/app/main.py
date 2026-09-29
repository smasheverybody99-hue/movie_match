"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.providers import usage as cost_log
from app.routers import health, me, movies, onboarding, ratings, recommendations, watchlist

settings = get_settings()


log = logging.getLogger(__name__)


async def startup_checks() -> None:
    """Refuse to start when EMBEDDING_DIM disagrees with the database (ADR 0006).

    An unreachable database is only logged: /health/db reports it, and the API should
    come up to say so. A reachable database with the wrong column size is fatal.
    """
    from sqlalchemy.exc import DBAPIError

    from app.db import SessionLocal
    from app.schema_checks import check_embedding_dim

    try:
        async with SessionLocal() as session:
            await check_embedding_dim(session, settings.embedding_dim)
    except (DBAPIError, OSError) as exc:
        log.warning("start-up schema check skipped, database unreachable: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup work goes here. Keep it fast.
    cost_log.configure()
    if settings.schema_check_on_startup and settings.database_url:
        await startup_checks()
    yield
    from app.db import engine

    await engine.dispose()


app = FastAPI(
    title="Movie Match API",
    version="0.1.0",
    description="AI-powered movie discovery.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(movies.router)
app.include_router(ratings.router)
app.include_router(watchlist.router)
app.include_router(me.router)
app.include_router(recommendations.router)
app.include_router(onboarding.router)
