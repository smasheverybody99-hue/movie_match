"""Ingesting a film twice leaves one row, carrying the newer data."""

import copy

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Credit, Genre, Keyword, Movie, MovieGenre, MovieKeyword, Person
from app.pipelines.ingest import SqlIngestStore
from app.pipelines.tmdb import to_film_record
from tests.conftest import load_fixture


async def _count(session: AsyncSession, model, *where) -> int:
    return await session.scalar(select(func.count()).select_from(model).where(*where)) or 0


async def test_same_film_twice_is_one_row_with_newer_data(db_session: AsyncSession) -> None:
    store = SqlIngestStore(db_session)
    payload = load_fixture("tmdb_movie_550.json")
    await store.upsert_film(to_film_record(payload))

    newer = copy.deepcopy(payload)
    newer["popularity"] = 99.9
    newer["overview"] = "Updated overview."
    newer["genres"] = [{"id": 18, "name": "Drama"}]  # Thriller dropped upstream
    newer["keywords"]["keywords"] = newer["keywords"]["keywords"][:2]
    newer["credits"]["cast"] = newer["credits"]["cast"][:1]
    await store.upsert_film(to_film_record(newer))

    assert await _count(db_session, Movie, Movie.id == 550) == 1
    movie = await db_session.get(Movie, 550, populate_existing=True)
    assert movie is not None
    assert movie.popularity == 99.9
    assert movie.overview == "Updated overview."
    assert movie.synced_at is not None

    # Links follow the newest payload: replaced, never accumulated.
    assert await _count(db_session, MovieGenre, MovieGenre.movie_id == 550) == 1
    assert await _count(db_session, MovieKeyword, MovieKeyword.movie_id == 550) == 2
    cast = await _count(db_session, Credit, Credit.movie_id == 550, Credit.department == "cast")
    assert cast == 1
    assert await _count(db_session, Credit, Credit.movie_id == 550, Credit.job == "Director") == 1


async def test_shared_lookups_are_not_duplicated(db_session: AsyncSession) -> None:
    store = SqlIngestStore(db_session)
    record = to_film_record(load_fixture("tmdb_movie_550.json"))
    await store.upsert_film(record)
    await store.upsert_film(record)

    assert await _count(db_session, Genre, Genre.id.in_([18, 53])) == 2
    assert await _count(db_session, Keyword, Keyword.id == 1541) == 1
    assert await _count(db_session, Person, Person.id == 287) == 1
    assert await _count(db_session, Credit, Credit.movie_id == 550) == len(record.credits)


async def test_renamed_genre_takes_the_new_name(db_session: AsyncSession) -> None:
    store = SqlIngestStore(db_session)
    payload = load_fixture("tmdb_movie_550.json")
    await store.upsert_film(to_film_record(payload))
    payload["genres"] = [{"id": 18, "name": "Drama (renamed)"}]
    await store.upsert_film(to_film_record(payload))

    name = await db_session.scalar(select(Genre.name).where(Genre.id == 18))
    assert name == "Drama (renamed)"


async def test_minimal_film_upserts(db_session: AsyncSession) -> None:
    """A film with no genres, keywords or credits still goes in cleanly."""
    await SqlIngestStore(db_session).upsert_film(to_film_record({"id": 8_000_001, "title": "Bare"}))
    assert await _count(db_session, Movie, Movie.id == 8_000_001) == 1
