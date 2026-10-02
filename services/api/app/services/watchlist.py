"""A user's watchlist: films to watch, and when they were watched."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie, WatchlistItem
from app.services.ratings import MovieNotFound


class NotOnWatchlist(LookupError):
    """The film is not on the user's watchlist."""


async def add(session: AsyncSession, user_id: uuid.UUID, movie_id: int) -> WatchlistItem:
    """Add a film. Adding it again changes nothing and returns the existing entry.

    One statement that always returns the row, new or existing. The no-op DO UPDATE is
    what makes RETURNING answer for an existing row too (DO NOTHING returns nothing). A
    separate SELECT after the commit raced a DELETE from the same user (Save, then
    unsave at once) and answered 500 (2026-10-02).
    """
    if await session.get(Movie, movie_id) is None:
        raise MovieNotFound(movie_id)
    stmt = insert(WatchlistItem).values(user_id=user_id, movie_id=movie_id)
    item = await session.scalar(
        stmt.on_conflict_do_update(
            constraint="uq_watchlist_user_movie", set_={"movie_id": stmt.excluded.movie_id}
        )
        .returning(WatchlistItem)
        .execution_options(populate_existing=True)
    )
    assert item is not None  # an upsert with RETURNING always yields its row
    await session.commit()
    return item


async def list_items(
    session: AsyncSession, user_id: uuid.UUID
) -> list[tuple[WatchlistItem, Movie]]:
    """Unwatched first, then watched; newest first inside each."""
    rows = await session.execute(
        select(WatchlistItem, Movie)
        .join(Movie, Movie.id == WatchlistItem.movie_id)
        .where(WatchlistItem.user_id == user_id)
        .order_by(
            WatchlistItem.watched_at.is_not(None),
            WatchlistItem.created_at.desc(),
            WatchlistItem.movie_id,
        )
    )
    return [(item, movie) for item, movie in rows.all()]


async def remove(session: AsyncSession, user_id: uuid.UUID, movie_id: int) -> None:
    result = await session.execute(
        delete(WatchlistItem)
        .where(WatchlistItem.user_id == user_id, WatchlistItem.movie_id == movie_id)
        .returning(WatchlistItem.id)
    )
    if result.first() is None:
        raise NotOnWatchlist(movie_id)
    await session.commit()


async def mark_watched(
    session: AsyncSession, user_id: uuid.UUID, movie_id: int, now: datetime | None = None
) -> WatchlistItem:
    """Record when the film was watched. Marking it again keeps the first date.

    One UPDATE ... RETURNING, so a removal in between is a clean NotOnWatchlist, not a
    stale-row error.
    """
    item = await session.scalar(
        update(WatchlistItem)
        .where(WatchlistItem.user_id == user_id, WatchlistItem.movie_id == movie_id)
        .values(watched_at=func.coalesce(WatchlistItem.watched_at, now or datetime.now(UTC)))
        .returning(WatchlistItem)
        .execution_options(populate_existing=True, synchronize_session=False)
    )
    if item is None:
        raise NotOnWatchlist(movie_id)
    await session.commit()
    return item
