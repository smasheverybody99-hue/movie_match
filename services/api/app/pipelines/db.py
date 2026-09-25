"""Database access for background jobs.

Jobs get their own engine: the app engine echoes SQL in development, which would bury
a 5,000-film run in log output.

Every job connection also sets two server-side timeouts. If the network drops mid-
transaction, the server keeps the orphaned session "idle in transaction", holding its
row locks, indefinitely - the next run then blocks on those locks. Observed on the
first catalogue run. The idle timeout lets the server reap such sessions itself; the
lock timeout makes a blocked write fail fast and be retried instead of hanging.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

SESSION_SETTINGS = {
    "idle_in_transaction_session_timeout": "60s",
    "lock_timeout": "20s",
}


def _apply_session_settings(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    for name, value in SESSION_SETTINGS.items():
        cursor.execute(f"SET {name} = '{value}'")
    cursor.close()


@asynccontextmanager
async def job_session() -> AsyncIterator[AsyncSession]:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    engine = create_async_engine(url, pool_pre_ping=True)
    event.listen(engine.sync_engine, "connect", _apply_session_settings)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            yield session
    finally:
        await engine.dispose()
