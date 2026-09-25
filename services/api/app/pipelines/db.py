"""Database access for background jobs.

Jobs get their own engine: the app engine echoes SQL in development, which would bury
a 5,000-film run in log output.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


@asynccontextmanager
async def job_session() -> AsyncIterator[AsyncSession]:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            yield session
    finally:
        await engine.dispose()
