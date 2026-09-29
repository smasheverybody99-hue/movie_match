"""The catalogue as the clients read it: search with filters, a film's detail, and the
caller's personal match for any film.

The personal match is the same formula as recommendations (matching.match_percentage,
docs/TZ.md FR-5) on the same stored numbers: users.taste_vector, users.taste_weights and
movie_traits.vector. A film page and the feed can never disagree about a film's match.
"""

import uuid
from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import Float, and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Credit, Genre, Movie, MovieGenre, MovieTraits, Person, Rating, User
from app.services.matching import match_percentage, top_reasons, weights_vector
from app.traits import TRAIT_KEYS

CAST_SHOWN = 5


@dataclass(frozen=True)
class TraitFilter:
    """Only films scoring at least `minimum` (0..100) on `key`."""

    key: str
    minimum: float

    def __post_init__(self) -> None:
        if self.key not in TRAIT_KEYS:
            raise ValueError(f"unknown trait key: {self.key}")
        if not 0 <= self.minimum <= 100:
            raise ValueError(f"trait minimum must be 0..100, got {self.minimum}")


@dataclass(frozen=True)
class SearchFilters:
    q: str = ""
    year_from: int | None = None
    year_to: int | None = None
    max_runtime: int | None = None
    traits: tuple[TraitFilter, ...] = ()


@dataclass(frozen=True)
class PersonalMatch:
    match: int
    reasons: list[str]


@dataclass(frozen=True)
class MovieDetail:
    movie: Movie
    scores: dict[str, float] | None
    summary: str | None
    genres: list[str] = field(default_factory=list)
    director: str | None = None
    cast: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Dna:
    """The caller's Movie DNA: their taste vector by trait key, and rating stats."""

    scores: dict[str, float]  # empty until the user has liked a scored film
    rating_count: int
    average_rating: float | None
    top_genre: str | None


async def search(session: AsyncSession, filters: SearchFilters, limit: int) -> list[Movie]:
    """Best known first. Trait filters leave out films that have no trait vector yet."""
    stmt = select(Movie).where(Movie.adult.is_(False))
    if filters.q:
        stmt = stmt.where(Movie.title.ilike(f"%{filters.q}%"))
    if filters.year_from is not None:
        stmt = stmt.where(extract("year", Movie.release_date) >= filters.year_from)
    if filters.year_to is not None:
        stmt = stmt.where(extract("year", Movie.release_date) <= filters.year_to)
    if filters.max_runtime is not None:
        stmt = stmt.where(Movie.runtime_minutes <= filters.max_runtime)
    if filters.traits:
        stmt = stmt.join(MovieTraits, MovieTraits.movie_id == Movie.id).where(
            and_(
                *(MovieTraits.scores[f.key].astext.cast(Float) >= f.minimum for f in filters.traits)
            )
        )
    stmt = stmt.order_by(Movie.popularity.desc().nullslast(), Movie.id).limit(limit)
    return list((await session.scalars(stmt)).all())


async def get_detail(session: AsyncSession, movie_id: int) -> MovieDetail | None:
    movie = await session.get(Movie, movie_id)
    if movie is None:
        return None
    traits = await session.get(MovieTraits, movie_id)
    genres = await session.scalars(
        select(Genre.name)
        .join(MovieGenre, MovieGenre.genre_id == Genre.id)
        .where(MovieGenre.movie_id == movie_id)
        .order_by(Genre.name)
    )
    people = await session.execute(
        select(Person.name, Credit.department, Credit.job)
        .join(Credit, Credit.person_id == Person.id)
        .where(Credit.movie_id == movie_id)
        .order_by(Credit.billing_order.asc().nullslast(), Credit.id)
    )
    director: str | None = None
    cast: list[str] = []
    for name, department, job in people.all():
        if job == "Director" and director is None:
            director = name
        elif department == "cast" and len(cast) < CAST_SHOWN:
            cast.append(name)
    return MovieDetail(
        movie=movie,
        scores={k: float(v) for k, v in traits.scores.items()} if traits else None,
        summary=traits.summary if traits else None,
        genres=list(genres.all()),
        director=director,
        cast=cast,
    )


async def personal_matches(
    session: AsyncSession, user_id: uuid.UUID, movie_ids: list[int]
) -> dict[int, PersonalMatch]:
    """The caller's match for each film that has traits. Empty without a taste profile."""
    if not movie_ids:
        return {}
    user = await session.get(User, user_id)
    if user is None or user.taste_vector is None or not user.taste_weights:
        return {}
    taste = [float(v) for v in user.taste_vector]
    weights = weights_vector(user.taste_weights)
    rows = await session.execute(
        select(MovieTraits.movie_id, MovieTraits.vector).where(MovieTraits.movie_id.in_(movie_ids))
    )
    matches = {}
    for movie_id, vector in rows.all():
        movie_vector = [float(v) for v in vector]
        matches[movie_id] = PersonalMatch(
            match=match_percentage(taste, weights, movie_vector),
            reasons=top_reasons(taste, movie_vector, weights=weights),
        )
    return matches


async def dna(session: AsyncSession, user_id: uuid.UUID) -> Dna:
    """The taste vector as {trait: score}, rounded to one decimal, plus rating stats.

    `top_genre` is the genre that appears on most of the user's rated films; ties go to
    the alphabetically first name, so the answer is stable.
    """
    user = await session.get(User, user_id, populate_existing=True)
    scores: dict[str, float] = {}
    if user is not None and user.taste_vector is not None:
        scores = {
            key: round(float(v), 1) for key, v in zip(TRAIT_KEYS, user.taste_vector, strict=True)
        }
    count, average = (
        await session.execute(
            select(func.count(), func.avg(Rating.score)).where(Rating.user_id == user_id)
        )
    ).one()
    genre_names = await session.scalars(
        select(Genre.name)
        .join(MovieGenre, MovieGenre.genre_id == Genre.id)
        .join(Rating, Rating.movie_id == MovieGenre.movie_id)
        .where(Rating.user_id == user_id)
    )
    tally = Counter(genre_names.all())
    top_genre = min(tally, key=lambda name: (-tally[name], name)) if tally else None
    return Dna(
        scores=scores,
        rating_count=count or 0,
        average_rating=round(float(average), 2) if average is not None else None,
        top_genre=top_genre,
    )
