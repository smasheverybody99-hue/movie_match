"""POST /events: a batch of what the client saw (Phase 5). HTTP only: the logic is in
app/services/events.py."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import current_user
from app.schemas import EventsIn, EventsOut
from app.services import events

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventsOut)
async def record_events(
    body: EventsIn,
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> EventsOut:
    """Write the batch in one transaction. One malformed event: 422, nothing written."""
    batch = [
        events.ClientEvent(
            type=e.type,
            at=e.at,
            movie_id=e.movie_id,
            source=e.source,
            props={"step": e.step} if e.step is not None else {},
        )
        for e in body.events
    ]
    try:
        recorded = await events.record_batch(session, user_id, batch)
    except events.EventRejected as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return EventsOut(recorded=recorded)
