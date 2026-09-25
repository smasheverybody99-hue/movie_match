"""Shared test fixtures.

Two kinds of test live here:

* Tests that need nothing but the app — they use `client`.
* Tests that need a real PostgreSQL with the pgvector extension — they use
  `db_session` and are skipped unless TEST_DATABASE_URL is set. There is no
  in-memory substitute: the schema uses pgvector and JSONB, so SQLite would
  test a different database than the one we ship.

Set it like this before running the full suite:

    export TEST_DATABASE_URL="postgresql+asyncpg://postgres:pw@localhost:5432/moviematch_test"
"""

from collections.abc import AsyncGenerator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.main import app

TEST_DATABASE_URL = get_settings().test_database_url

requires_db = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is not set — database-backed test skipped",
)


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """FastAPI test client with the application lifespan running."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """A session against the test database, rolled back after each test.

    The outer transaction is never committed, so tests cannot leak rows into
    each other even when the code under test calls `commit()`.
    """
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set")

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=None)
    connection = await engine.connect()
    transaction = await connection.begin()
    maker = async_sessionmaker(bind=connection, expire_on_commit=False)

    async with maker() as session:
        try:
            yield session
        finally:
            await session.close()

    await transaction.rollback()
    await connection.close()
    await engine.dispose()
