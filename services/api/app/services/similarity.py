"""Nearest neighbours by embedding, with hard filters.

Retrieval only: candidates come back with their trait vectors attached so Phase 2 can
rank them by trait distance. Distance is pgvector cosine distance (`<=>`), served by the
HNSW index on movie_embeddings.
"""

from dataclasses import dataclass

from sqlalchemy import Float, cast, extract, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie, MovieEmbedding, MovieTraits

# Filters are applied after the index proposes candidates, so ask the index for more
# than `limit` when filtering. 200 is ample for a catalogue of thousands.
EF_SEARCH = 200


class NoEmbedding(LookupError):
    """The seed film is unknown or has no embedding yet."""


@dataclass(frozen=True)
class SimilarityFilters:
    year_min: int | None = None
    year_max: int | None = None
    runtime_min: int | None = None
    runtime_max: int | None = None
    languages: tuple[str, ...] = ()
    max_violence: float | None = None


@dataclass(frozen=True)
class SimilarFilm:
    movie_id: int
    title: str
    year: int | None
    distance: float  # cosine distance, 0 = identical direction
    traits: list[float]  # ordered as app.traits.TRAIT_KEYS


async def find_similar(
    session: AsyncSession,
    movie_id: int,
    limit: int = 20,
    filters: SimilarityFilters | None = None,
) -> list[SimilarFilm]:
    """Films closest to `movie_id`, nearest first, excluding the film itself."""
    filters = filters or SimilarityFilters()
    seed = await session.scalar(
        select(MovieEmbedding.embedding).where(MovieEmbedding.movie_id == movie_id)
    )
    if seed is None:
        raise NoEmbedding(movie_id)

    distance = MovieEmbedding.embedding.cosine_distance(seed).label("distance")
    stmt = (
        select(Movie.id, Movie.title, Movie.release_date, MovieTraits.vector, distance)
        .join(MovieEmbedding, MovieEmbedding.movie_id == Movie.id)
        .join(MovieTraits, MovieTraits.movie_id == Movie.id)
        .where(Movie.id != movie_id)
    )
    year = extract("year", Movie.release_date)
    if filters.year_min is not None:
        stmt = stmt.where(year >= filters.year_min)
    if filters.year_max is not None:
        stmt = stmt.where(year <= filters.year_max)
    if filters.runtime_min is not None:
        stmt = stmt.where(Movie.runtime_minutes >= filters.runtime_min)
    if filters.runtime_max is not None:
        stmt = stmt.where(Movie.runtime_minutes <= filters.runtime_max)
    if filters.languages:
        stmt = stmt.where(Movie.original_language.in_(filters.languages))
    if filters.max_violence is not None:
        violence = cast(MovieTraits.scores["violence"].astext, Float)
        stmt = stmt.where(violence <= filters.max_violence)
    stmt = stmt.order_by(distance, Movie.id).limit(limit)

    await session.execute(text(f"SET LOCAL hnsw.ef_search = {EF_SEARCH}"))
    rows = (await session.execute(stmt)).all()
    return [
        SimilarFilm(
            movie_id=row.id,
            title=row.title,
            year=row.release_date.year if row.release_date else None,
            distance=float(row.distance),
            traits=[float(v) for v in row.vector],
        )
        for row in rows
    ]
