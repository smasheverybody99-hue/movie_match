"""The caller's own account. HTTP only: the logic is in app/services/users.py."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import current_user
from app.schemas import MeOut
from app.services import users
from app.services.recommend import MIN_RATINGS

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
async def get_me(
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
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
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete the account's data: ratings, watchlist, dismissals, explanations, profile."""
    await users.delete_user(session, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
