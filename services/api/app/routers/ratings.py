"""The caller's ratings. HTTP only: the logic is in app/services/ratings.py."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import current_user
from app.models import Rating
from app.schemas import RatingIn, RatingOut
from app.services import ratings

router = APIRouter(prefix="/ratings", tags=["ratings"])


def _out(rating: Rating) -> RatingOut:
    return RatingOut(
        movie_id=rating.movie_id,
        score=rating.score,
        liked_aspects=rating.liked_aspects or [],
        rated_at=rating.updated_at,
    )


@router.post("", response_model=RatingOut)
async def rate(
    body: RatingIn,
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> RatingOut:
    """Rate a film, or change the rating. Recomputes the caller's taste profile."""
    try:
        rating = await ratings.rate(session, user_id, body.movie_id, body.score, body.liked_aspects)
    except ratings.MovieNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found") from exc
    return _out(rating)


@router.get("", response_model=list[RatingOut])
async def list_ratings(
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[RatingOut]:
    return [_out(r) for r in await ratings.list_ratings(session, user_id)]


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unrate(
    movie_id: int = Path(gt=0),
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        await ratings.unrate(session, user_id, movie_id)
    except ratings.RatingNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rating not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
