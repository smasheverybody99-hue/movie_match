"""A user's ratings. Every change recomputes the taste profile in the same transaction."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie, Rating
from app.services.taste import recompute_taste


class MovieNotFound(LookupError):
    """No such film in the catalogue."""


class RatingNotFound(LookupError):
    """The user has not rated this film."""


async def rate(
    session: AsyncSession,
    user_id: uuid.UUID,
    movie_id: int,
    score: float,
    liked_aspects: Sequence[str] = (),
) -> Rating:
    """Create or replace the user's rating of a film: one rating per (user, film)."""
    if await session.get(Movie, movie_id) is None:
        raise MovieNotFound(movie_id)
    values = {
        "user_id": user_id,
        "movie_id": movie_id,
        "score": score,
        "liked_aspects": list(liked_aspects),
    }
    insert_stmt = insert(Rating).values(**values)
    upsert = insert_stmt.on_conflict_do_update(
        constraint="uq_rating_user_movie",
        set_={
            "score": insert_stmt.excluded.score,
            "liked_aspects": insert_stmt.excluded.liked_aspects,
            "updated_at": func.now(),
        },
    ).returning(Rating)
    rating = (await session.scalars(upsert, execution_options={"populate_existing": True})).one()
    await recompute_taste(session, user_id)
    await session.commit()
    return rating


async def unrate(session: AsyncSession, user_id: uuid.UUID, movie_id: int) -> None:
    result = await session.execute(
        delete(Rating)
        .where(Rating.user_id == user_id, Rating.movie_id == movie_id)
        .returning(Rating.id)
    )
    if result.first() is None:
        raise RatingNotFound(movie_id)
    await recompute_taste(session, user_id)
    await session.commit()


async def list_ratings(session: AsyncSession, user_id: uuid.UUID) -> list[Rating]:
    """Most recently rated first."""
    rows = await session.scalars(
        select(Rating)
        .where(Rating.user_id == user_id)
        .order_by(Rating.updated_at.desc(), Rating.movie_id)
    )
    return list(rows.all())
