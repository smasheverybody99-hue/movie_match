"""The caller's own account. HTTP only: the logic is in app/services/users.py."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_session
from app.deps import current_user
from app.schemas import MeOut, MovieDnaOut
from app.services import movies, users
from app.services.recommend import MIN_RATINGS

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
async def get_me(
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MeOut:
    profile = await users.get_profile(session, user_id)
    user = profile.user
    return MeOut(
        id=user.id,
        created_at=user.created_at,
        rating_count=profile.rating_count,
        ratings_needed=max(MIN_RATINGS - profile.rating_count, 0),
        has_taste_profile=user.taste_vector is not None,
        taste_updated_at=user.taste_updated_at,
        data_notice_required=settings.data_notice_required,
        data_notice_accepted_at=user.data_notice_accepted_at,
        assistant_enabled=settings.assistant_enabled,
    )


@router.post("/data-notice", status_code=status.HTTP_204_NO_CONTENT)
async def accept_data_notice(
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """The user read the data notice and accepted it. Accepting again keeps the first
    time (ADR 0004, the alpha's free-tier exception)."""
    await users.accept_data_notice(session, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/dna", response_model=MovieDnaOut)
async def get_dna(
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> MovieDnaOut:
    """The caller's Movie DNA (FR-7). Below 10 ratings `ratings_needed` says how many more."""
    dna = await movies.dna(session, user_id)
    return MovieDnaOut(
        scores=dna.scores,
        summary=None,
        rating_count=dna.rating_count,
        ratings_needed=max(MIN_RATINGS - dna.rating_count, 0),
        average_rating=dna.average_rating,
        top_genre=dna.top_genre,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete the account's data: ratings, watchlist, dismissals, explanations, profile."""
    await users.delete_user(session, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
