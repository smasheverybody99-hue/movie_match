"""A user's watchlist: films to watch, and when they were watched."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie, WatchlistItem
from app.services.ratings import MovieNotFound


class NotOnWatchlist(LookupError):
    """The film is not on the user's watchlist."""


async def add(session: AsyncSession, user_id: uuid.UUID, movie_id: int) -> WatchlistItem:
    """Add a film. Adding it again changes nothing and returns the existing entry."""
    if await session.get(Movie, movie_id) is None:
        raise MovieNotFound(movie_id)
    await session.execute(
        insert(WatchlistItem)
        .values(user_id=user_id, movie_id=movie_id)
        .on_conflict_do_nothing(constraint="uq_watchlist_user_movie")
    )
    await session.commit()
    return await _get(session, user_id, movie_id)


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
    """Record when the film was watched. Marking it again keeps the first date."""
    item = await _get(session, user_id, movie_id)
    if item.watched_at is None:
        item.watched_at = now or datetime.now(UTC)
        await session.commit()
    return item


async def _get(session: AsyncSession, user_id: uuid.UUID, movie_id: int) -> WatchlistItem:
    item = await session.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id, WatchlistItem.movie_id == movie_id
        )
    )
    if item is None:
        raise NotOnWatchlist(movie_id)
    return item
