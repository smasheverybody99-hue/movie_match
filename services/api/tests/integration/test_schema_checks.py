"""EMBEDDING_DIM against the real column in the test database (ADR 0006)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models import EMBEDDING_DIM
from app.schema_checks import (
    EmbeddingDimMismatch,
    check_embedding_dim,
    embedding_column_dim,
    mismatch_message,
)


async def test_the_column_size_is_read_from_the_database(db_session: AsyncSession) -> None:
    assert await embedding_column_dim(db_session) == 1536 == EMBEDDING_DIM


async def test_the_configured_size_passes(db_session: AsyncSession) -> None:
    await check_embedding_dim(db_session, Settings(_env_file=None).embedding_dim)


@pytest.mark.parametrize("configured", [1024, 3072])
async def test_another_size_is_an_explicit_error(db_session: AsyncSession, configured: int) -> None:
    with pytest.raises(EmbeddingDimMismatch) as raised:
        await check_embedding_dim(db_session, configured)
    message = str(raised.value)
    assert f"EMBEDDING_DIM={configured}" in message
    assert "vector(1536)" in message
    assert "migration" in message and "re-embed" in message


def test_above_the_hnsw_limit_the_message_says_halfvec() -> None:
    assert "halfvec" in mismatch_message(3072, 1536)
    assert "halfvec" not in mismatch_message(1024, 1536)


async def test_the_api_refuses_to_start_on_a_mismatch(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main.startup_checks raises on a real mismatch rather than logging it."""
    from contextlib import asynccontextmanager

    import app.db
    from app import main

    @asynccontextmanager
    async def on_test_db():  # type: ignore[no-untyped-def]
        yield db_session

    monkeypatch.setattr(app.db, "SessionLocal", on_test_db)
    monkeypatch.setattr(main.settings, "embedding_dim", 1024)
    with pytest.raises(EmbeddingDimMismatch):
        await main.startup_checks()
