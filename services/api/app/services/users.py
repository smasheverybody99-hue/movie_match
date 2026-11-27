"""The local mirror of Supabase users."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, text, update
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


async def accept_data_notice(
    session: AsyncSession, user_id: uuid.UUID, now: datetime | None = None
) -> None:
    """Record when the user accepted the data notice; the first time stays."""
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            data_notice_accepted_at=func.coalesce(
                User.data_notice_accepted_at, now or datetime.now(UTC)
            )
        )
        .execution_options(synchronize_session=False)
    )
    await session.commit()


async def has_auth_schema(session: AsyncSession) -> bool:
    """Whether this database is a Supabase one, with the sign-in records in `auth.users`.

    The CI database is plain Postgres without it; the main and test Supabase projects
    have it."""
    return bool(await session.scalar(text("SELECT to_regclass('auth.users') IS NOT NULL")))


async def delete_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Delete the account completely: the app's rows and the Supabase sign-in record.

    Every user table references users.id with ON DELETE CASCADE, so deleting the users
    row removes ratings, watchlist, dismissals, explanations, assistant turns and usage,
    events and feedback. Then the sign-in record in `auth.users` (it holds the email)
    goes too; Supabase's own tables (identities, sessions, MFA, one-time tokens) cascade
    from it. Both happen in one transaction: if the sign-in record cannot be deleted,
    nothing is, and the caller gets an error instead of a half-deleted account.

    It runs as the API's own database role, which may delete from `auth.users` (checked
    on the main database, 2026-11-27), so no Supabase service key is needed.
    """
    await session.execute(delete(User).where(User.id == user_id))
    if await has_auth_schema(session):
        await session.execute(text("DELETE FROM auth.users WHERE id = :id"), {"id": user_id})
    await session.commit()
