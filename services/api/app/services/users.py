"""The local mirror of Supabase users."""

import uuid
from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rating, User


@dataclass(frozen=True)
class Profile:
    user: User
    rating_count: int


async def ensure_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Create the user's row if it does not exist yet. Safe to call on every request."""
    await session.execute(
        insert(User).values(id=user_id).on_conflict_do_nothing(index_elements=[User.id])
    )
    await session.commit()


async def get_profile(session: AsyncSession, user_id: uuid.UUID) -> Profile:
    user = await session.get(User, user_id, populate_existing=True)
    if user is None:
        raise LookupError(f"no user {user_id}")
    count = await session.scalar(
        select(func.count()).select_from(Rating).where(Rating.user_id == user_id)
    )
    return Profile(user=user, rating_count=count or 0)


async def delete_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Delete the user and, through ON DELETE CASCADE, every row that belongs to them.

    Ratings, watchlist, dismissals and cached explanations all reference users.id with
    ON DELETE CASCADE. The Supabase Auth identity itself is not touched here.
    """
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
