"""The caller's watchlist. HTTP only: the logic is in app/services/watchlist.py."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import current_user
from app.models import Movie, WatchlistItem
from app.schemas import MovieOut, WatchlistIn, WatchlistItemOut
from app.services import watchlist
from app.services.ratings import MovieNotFound

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def _out(item: WatchlistItem, movie: Movie) -> WatchlistItemOut:
    return WatchlistItemOut(
        movie=MovieOut.model_validate(movie),
        added_at=item.created_at,
        watched_at=item.watched_at,
    )


@router.get("", response_model=list[WatchlistItemOut])
async def list_watchlist(
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[WatchlistItemOut]:
    return [_out(item, movie) for item, movie in await watchlist.list_items(session, user_id)]


@router.post("", response_model=WatchlistItemOut)
async def add_to_watchlist(
    body: WatchlistIn,
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> WatchlistItemOut:
    """Add a film. Adding it twice is harmless and returns the same entry."""
    try:
        item = await watchlist.add(session, user_id, body.movie_id)
    except MovieNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found") from exc
    return await _with_movie(session, item)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    movie_id: int = Path(gt=0),
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        await watchlist.remove(session, user_id, movie_id)
    except watchlist.NotOnWatchlist as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not on the watchlist") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{movie_id}/watched", response_model=WatchlistItemOut)
async def mark_watched(
    movie_id: int = Path(gt=0),
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> WatchlistItemOut:
    try:
        item = await watchlist.mark_watched(session, user_id, movie_id)
    except watchlist.NotOnWatchlist as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not on the watchlist") from exc
    return await _with_movie(session, item)


async def _with_movie(session: AsyncSession, item: WatchlistItem) -> WatchlistItemOut:
    movie = await session.get(Movie, item.movie_id)
    assert movie is not None  # the foreign key guarantees it
    return _out(item, movie)
