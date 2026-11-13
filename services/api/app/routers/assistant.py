"""The assistant: POST /assistant/chat, answered as a Server-Sent Events stream (FR-8).

HTTP only: the logic is in app/services/assistant.py. Everything that can fail before the
model is called answers with an ordinary status (401, 422, 429, 503); once the stream has
started, it ends with a `done` or an `error` event.

Events, each `event: <name>` + `data: <json>`:

    text       {"text": "..."}               part of the answer, in order
    card       AssistantCardOut              a film, where it stands in the answer
    followups  {"items": ["...", ...]}       two or three chips
    refusal    {"reason": "off_topic"|"leak"}  the client shows its own fixed text
    reset      {}                            drop what this answer showed: a call broke
                                             off and runs again; the events before it
                                             are sent again, then the new attempt
    error      {"reason": "failed"|"blocked"|"timeout"}  "timeout": the message passed
                                             its time limit; the client says it is busy
    done       {}
"""

import json
import time as clock
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_session
from app.deps import current_user, current_user_id, get_assistant
from app.providers.base import Assistant
from app.routers.common import movie_out
from app.schemas import AssistantCardOut, AssistantChatIn, AssistantLimitOut
from app.services import assistant as service
from app.services import movies

router = APIRouter(prefix="/assistant", tags=["assistant"])


def sse(name: str, data: object) -> str:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _events(
    session: AsyncSession, events: AsyncIterator[service.Event]
) -> AsyncIterator[str]:
    async for event in events:
        if isinstance(event, service.Text):
            yield sse("text", {"text": event.text})
        elif isinstance(event, service.Card):
            hit = event.hit
            genres = await movies.genre_names(session, [hit.movie.id])
            card = AssistantCardOut(
                movie=movie_out(hit.movie, genres), match=hit.match, band=hit.band
            )
            yield sse("card", card.model_dump(mode="json"))
        elif isinstance(event, service.Followups):
            yield sse("followups", {"items": event.items})
        elif isinstance(event, service.Refusal):
            yield sse("refusal", {"reason": event.reason})
        elif isinstance(event, service.Failed):
            yield sse("error", {"reason": event.reason})
        elif isinstance(event, service.Reset):
            yield sse("reset", {})
        else:
            yield sse("done", {})


async def _arrived() -> float:
    """When the request reached the handler's dependencies (the body is already read).
    Declared first in `chat`, so it runs before authentication."""
    return clock.perf_counter()


async def _verified(_: uuid.UUID = Depends(current_user_id)) -> float:
    """When the token was verified: `current_user_id` is cached per request, so the
    `current_user` that follows reuses it and only adds the users row."""
    return clock.perf_counter()


@router.post(
    "/chat",
    response_class=StreamingResponse,
    response_model=None,
    responses={
        200: {"content": {"text/event-stream": {}}, "description": "The answer, streamed"},
        429: {"model": AssistantLimitOut, "description": "Today's messages are used up"},
        503: {"description": "The assistant is not configured"},
    },
)
async def chat(
    body: AssistantChatIn,
    arrived: float = Depends(_arrived),
    verified: float = Depends(_verified),
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
    assistant: Assistant | None = Depends(get_assistant),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse | JSONResponse:
    if assistant is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The assistant is not configured")
    # Everything before the stream, for the timing line: FR-8's 2 s is counted by the
    # viewer from the moment they send, not from when the model is called.
    user_ready = clock.perf_counter()
    cap = settings.assistant_daily_calls_per_user
    resets_at = await service.claim(session, user_id, cap)
    claimed = clock.perf_counter()
    if resets_at is not None:
        body_out = AssistantLimitOut(
            detail="Daily assistant limit reached", limit=cap, resets_at=resets_at
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=body_out.model_dump(mode="json"),
            headers={"Retry-After": str(_seconds_until(resets_at))},
        )
    if body.new_conversation:
        await service.forget(session, user_id)
    before = {
        "jwt": verified - arrived,
        "user": user_ready - verified,
        "claim": claimed - user_ready,
        "forget": clock.perf_counter() - claimed,
    }
    events = service.chat(session, user_id, body.message, body.lang, assistant, before=before)
    return StreamingResponse(
        _events(session, events),
        media_type="text/event-stream",
        # No proxy may hold the stream back: the first words must show within 2 s (FR-8).
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _seconds_until(moment: datetime) -> int:
    return max(int((moment - datetime.now(UTC)).total_seconds()), 1)
