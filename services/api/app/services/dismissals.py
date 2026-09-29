"""Films a user said "not for me" to. Recommendations exclude them."""

import uuid

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Dismissal, Movie
from app.services.ratings import MovieNotFound


class NotDismissed(LookupError):
    """The user has not dismissed this film."""


async def dismiss(session: AsyncSession, user_id: uuid.UUID, movie_id: int) -> None:
    """Dismiss a film. Dismissing it again changes nothing."""
    if await session.get(Movie, movie_id) is None:
        raise MovieNotFound(movie_id)
    await session.execute(
        insert(Dismissal)
        .values(user_id=user_id, movie_id=movie_id)
        .on_conflict_do_nothing(index_elements=[Dismissal.user_id, Dismissal.movie_id])
    )
    await session.commit()


async def undismiss(session: AsyncSession, user_id: uuid.UUID, movie_id: int) -> None:
    result = await session.execute(
        delete(Dismissal)
        .where(Dismissal.user_id == user_id, Dismissal.movie_id == movie_id)
        .returning(Dismissal.movie_id)
    )
    if result.first() is None:
        raise NotDismissed(movie_id)
    await session.commit()
