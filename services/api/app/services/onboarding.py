"""Cold start: films to rate first, spread across genres, the best-known first.

Each genre contributes its most popular scored films; the list takes them in turns
(genre 1's first, genre 2's first, ..., then genre 1's second, ...), skipping repeats,
so the first screen is not twenty action films. Only films with a trait vector are
offered: rating one of those is what builds the taste profile. Films the user has
already rated are left out, so a user who comes back resumes where they stopped (FR-3).
"""

import uuid
from itertools import zip_longest

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Genre, Movie, MovieGenre, MovieTraits, Rating

PER_GENRE = 8


def interleave(by_genre: list[list[int]], limit: int) -> list[int]:
    """Round-robin over the genre lists, first occurrence wins, at most `limit` ids."""
    picked: list[int] = []
    seen: set[int] = set()
    for turn in zip_longest(*by_genre):
        for movie_id in turn:
            if movie_id is not None and movie_id not in seen:
                seen.add(movie_id)
                picked.append(movie_id)
                if len(picked) == limit:
                    return picked
    return picked


async def onboarding_films(session: AsyncSession, user_id: uuid.UUID, limit: int) -> list[Movie]:
    rated = select(Rating.movie_id).where(Rating.user_id == user_id)
    rank = (
        func.row_number()
        .over(
            partition_by=MovieGenre.genre_id,
            order_by=(Movie.popularity.desc().nullslast(), Movie.id),
        )
        .label("rank")
    )
    ranked = (
        select(MovieGenre.genre_id, Movie.id.label("movie_id"), Movie.popularity, rank)
        .join(Movie, Movie.id == MovieGenre.movie_id)
        .join(MovieTraits, MovieTraits.movie_id == Movie.id)
        .where(Movie.adult.is_(False), Movie.id.not_in(rated))
        .subquery()
    )
    rows = await session.execute(
        select(ranked.c.genre_id, ranked.c.movie_id, ranked.c.popularity)
        .join(Genre, Genre.id == ranked.c.genre_id)
        .where(ranked.c.rank <= PER_GENRE)
        .order_by(ranked.c.genre_id, ranked.c.rank)
    )
    by_genre: dict[int, list[int]] = {}
    top_popularity: dict[int, float] = {}
    for genre_id, movie_id, popularity in rows.all():
        by_genre.setdefault(genre_id, []).append(movie_id)
        top_popularity.setdefault(genre_id, popularity or 0.0)
    # Genres in order of their most popular film, so the best-known lists lead.
    order = sorted(by_genre, key=lambda g: (-top_popularity[g], g))
    ids = interleave([by_genre[g] for g in order], limit)
    if not ids:
        return []
    movies = {m.id: m for m in await session.scalars(select(Movie).where(Movie.id.in_(ids)))}
    return [movies[i] for i in ids]
