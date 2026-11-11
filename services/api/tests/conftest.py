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

import os

# Before anything imports app.config: the API's start-up schema check would otherwise
# connect to DATABASE_URL (the real database) whenever a test starts the app. Tests of
# the check call it directly against the test database.
os.environ.setdefault("SCHEMA_CHECK_ON_STARTUP", "false")

import json
import sys
from collections.abc import AsyncGenerator, AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

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


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> Any:
    """A recorded or hand-written response from tests/fixtures/."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def migrated_test_db() -> None:
    """Bring the throwaway test database to the latest schema, once per test run."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set")
    from alembic import command

    from tests.test_migrations import _alembic_config

    command.upgrade(_alembic_config(TEST_DATABASE_URL), "head")


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """FastAPI test client with the application lifespan running."""
    with TestClient(app) as test_client:
        yield test_client


@asynccontextmanager
async def rolled_back_session() -> AsyncIterator[AsyncSession]:
    """A session against the test database whose work is all thrown away at the end.

    The outer transaction is never committed, so tests cannot leak rows into
    each other even when the code under test calls `commit()`.
    """
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=None)
    connection = await engine.connect()
    transaction = await connection.begin()
    # Each commit() inside a test becomes a savepoint, and rollback() returns to the last
    # one - the same semantics the code sees in production, all inside the outer
    # transaction that is thrown away at the end.
    maker = async_sessionmaker(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )

    async with maker() as session:
        try:
            yield session
        finally:
            await session.close()

    await transaction.rollback()
    await connection.close()
    await engine.dispose()


@pytest.fixture
async def db_session(migrated_test_db: None) -> AsyncGenerator[AsyncSession, None]:
    """A session against the test database, rolled back after each test."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set")
    async with rolled_back_session() as session:
        yield session


def _workflow_escape(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _annotate(report: pytest.TestReport | pytest.CollectReport, when: str) -> None:
    """On GitHub Actions, a failure also becomes an `::error` annotation.

    The run log answers 403 without a GitHub login, and `gh` is not installed on the dev
    machine, so a red gate could not be read back. Annotations are served by the public
    check-runs API. GitHub keeps at most 10 error annotations per step. The command must
    start a line, and pytest's progress dots do not end theirs, hence the leading newline.
    """
    if not report.failed or os.environ.get("GITHUB_ACTIONS") != "true":
        return
    crash = getattr(report.longrepr, "reprcrash", None)
    message = getattr(crash, "message", None) or str(report.longrepr).strip()[-800:]
    if isinstance(report, pytest.TestReport):
        path, line = report.location[0], report.location[1] or 0
    else:
        path, line = report.nodeid.split("::")[0], 0
    title = _workflow_escape(f"{when}: {report.nodeid}"[:200]).replace(",", "%2C")
    annotation = (
        f"::error file=services/api/{path},line={line + 1},title={title}"
        f"::{_workflow_escape(message[:1000])}"
    )
    print(f"\n{annotation}", file=sys.__stdout__, flush=True)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    _annotate(report, report.when)


def pytest_collectreport(report: pytest.CollectReport) -> None:
    _annotate(report, "collect")


@pytest.fixture(autouse=True)
def _fresh_reason_stats() -> Iterator[None]:
    """Each test seeds its own catalogue: never reuse another test's trait statistics or
    band cuts."""
    from app.services import bands, reasons

    reasons.clear_cache()
    bands.clear_cache()
    yield
    reasons.clear_cache()
    bands.clear_cache()
