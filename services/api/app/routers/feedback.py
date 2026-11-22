"""POST /feedback: "this recommendation was wrong" (Phase 5). HTTP only: the logic is in
app/services/feedback.py."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import current_user
from app.schemas import FeedbackIn
from app.services import feedback
from app.services.ratings import MovieNotFound

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def mark_wrong(
    body: FeedbackIn,
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Store it, or replace the earlier press for this film. Recommendations stay as
    they are."""
    try:
        await feedback.mark_wrong(session, user_id, body.movie_id, body.source, body.reason)
    except MovieNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
