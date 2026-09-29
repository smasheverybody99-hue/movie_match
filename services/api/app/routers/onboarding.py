"""Cold start. HTTP only: the logic is in app/services/onboarding.py."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import current_user
from app.schemas import MovieOut
from app.services.onboarding import onboarding_films

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/films", response_model=list[MovieOut])
async def get_onboarding_films(
    limit: int = Query(30, ge=1, le=100),
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[MovieOut]:
    """Films to rate first: well known, spread across genres, not yet rated by the caller."""
    return [MovieOut.model_validate(m) for m in await onboarding_films(session, user_id, limit)]
