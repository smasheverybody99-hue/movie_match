"""Checks that the configuration matches the database it runs against.

The embedding size is a setting (EMBEDDING_DIM) because providers differ: 1,024, 1,536
and 3,072 are all common. pgvector stores the size in the column type, so a provider
switch that changes it cannot be absorbed silently - vectors would fail to insert, or
worse, a query vector of one size would be compared with stored vectors of another.
This makes the mismatch an explicit error at start, with the way out in the message.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# pgvector's HNSW index takes `vector` columns up to 2,000 dimensions; beyond that the
# column (or the index expression) has to be `halfvec`.
HNSW_MAX_VECTOR_DIM = 2000


class EmbeddingDimMismatch(RuntimeError):
    pass


async def embedding_column_dim(session: AsyncSession) -> int | None:
    """The size in the type of movie_embeddings.embedding; None if the table is missing."""
    row = await session.execute(
        text(
            "SELECT a.atttypmod FROM pg_attribute a "
            "WHERE a.attrelid = to_regclass('movie_embeddings') "
            "AND a.attname = 'embedding' AND NOT a.attisdropped"
        )
    )
    value = row.scalar_one_or_none()
    return int(value) if value is not None and value > 0 else None


def mismatch_message(configured: int, column: int) -> str:
    message = (
        f"EMBEDDING_DIM={configured}, but movie_embeddings.embedding is vector({column}). "
        f"Either set EMBEDDING_DIM={column}, or change the column: a new Alembic migration "
        f"that re-creates it as vector({configured}) and its HNSW index, then re-embed every "
        "film (stored vectors of the old size cannot be converted). See ADR 0006."
    )
    if configured > HNSW_MAX_VECTOR_DIM:
        message += (
            f" Note: HNSW indexes `vector` only up to {HNSW_MAX_VECTOR_DIM} dimensions; "
            f"{configured} needs a halfvec column or index."
        )
    return message


async def check_embedding_dim(session: AsyncSession, configured: int) -> None:
    """Raise EmbeddingDimMismatch unless the column holds `configured`-d vectors.

    A database without the table (migrations not run yet) passes: there is nothing to
    disagree with, and `alembic upgrade` creates the column from the migration.
    """
    column = await embedding_column_dim(session)
    if column is not None and column != configured:
        raise EmbeddingDimMismatch(mismatch_message(configured, column))
