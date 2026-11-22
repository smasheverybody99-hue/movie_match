"""What testers do, for the closed alpha's metrics (Phase 5, app/pipelines/metrics.py).

Two ways in:

* The server records what it already handles - a rating, a watchlist add, a film marked
  watched, an assistant message, onboarding finished - with `add()`, in the same
  transaction as the action itself, so the event and the action are stored or lost
  together (user decision, 2026-11-17).
* The client sends what only it can see - a recommendation shown or clicked, an
  onboarding step - in batches (`POST /events`, `record_batch()`). A batch is written in
  one transaction; one malformed event rejects the whole batch, nothing is dropped.

No event carries text the user typed: a type, a film id, a source from a fixed set and
`props` with enumerated values only. The assistant's event does not hold the question.
"""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal, get_args

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, Movie

EventType = Literal[
    "recommendation_shown",
    "recommendation_clicked",
    "added_to_watchlist",
    "marked_watched",
    "rated",
    "assistant_query",
    "onboarding_step",
    "onboarding_done",
]
EVENT_TYPES: frozenset[str] = frozenset(get_args(EventType))

# Only these come from the client. The rest are the server's: a client cannot claim a
# rating it never made, or count one twice.
ClientEventType = Literal["recommendation_shown", "recommendation_clicked", "onboarding_step"]
CLIENT_EVENT_TYPES: frozenset[str] = frozenset(get_args(ClientEventType))

# Where a recommendation was shown: the Home sections (schemas.SectionKey) and the
# assistant's cards.
Source = Literal["for_you", "because_you_loved", "under_90", "outside_usual", "assistant"]
SOURCES: frozenset[str] = frozenset(get_args(Source))

OnboardingStep = Literal["pick", "rate", "done"]
ONBOARDING_STEPS: frozenset[str] = frozenset(get_args(OnboardingStep))

# How far a client's clock may put an event from the server's. Past: a batch kept while
# offline still counts for a week. Future: clock drift only.
MAX_AGE = timedelta(days=7)
MAX_AHEAD = timedelta(minutes=5)
MAX_BATCH = 50


class EventRejected(ValueError):
    """A batch with an event that is not well formed. Nothing of the batch is written."""


@dataclass(frozen=True)
class ClientEvent:
    """One event as the client sent it, already parsed (schemas.EventIn)."""

    type: str
    at: datetime
    movie_id: int | None = None
    source: str | None = None
    props: Mapping[str, str] = field(default_factory=dict)


def add(
    session: AsyncSession,
    user_id: uuid.UUID,
    type: EventType,
    *,
    movie_id: int | None = None,
    source: Source | None = None,
    props: Mapping[str, str] | None = None,
    at: datetime | None = None,
) -> Event:
    """Add one event to the session. The caller commits, with the action it belongs to."""
    if type not in EVENT_TYPES:
        raise EventRejected(f"unknown event type {type!r}")
    event = Event(
        user_id=user_id,
        type=type,
        movie_id=movie_id,
        source=source,
        props=dict(props or {}),
        occurred_at=at or datetime.now(UTC),
    )
    session.add(event)
    return event


def check(event: ClientEvent, now: datetime) -> None:
    """Raise EventRejected unless the event is well formed for its type.

    recommendation_shown / _clicked: a film and a source, no props.
    onboarding_step: props {"step": pick|rate|done}, no film, no source.
    """
    if event.type not in CLIENT_EVENT_TYPES:
        raise EventRejected(f"{event.type!r} is not an event the client sends")
    if event.at.tzinfo is None:
        raise EventRejected("the time has no time zone")
    if not now - MAX_AGE <= event.at <= now + MAX_AHEAD:
        raise EventRejected(f"the time {event.at.isoformat()} is too far from the server's")
    if event.type == "onboarding_step":
        if event.movie_id is not None or event.source is not None:
            raise EventRejected("onboarding_step takes no film and no source")
        if set(event.props) != {"step"} or event.props["step"] not in ONBOARDING_STEPS:
            raise EventRejected("onboarding_step needs props {step: pick|rate|done}")
        return
    if event.movie_id is None or event.movie_id <= 0:
        raise EventRejected(f"{event.type} needs a film")
    if event.source not in SOURCES:
        raise EventRejected(f"{event.type} needs a source from {sorted(SOURCES)}")
    if event.props:
        raise EventRejected(f"{event.type} takes no props")


async def record_batch(
    session: AsyncSession,
    user_id: uuid.UUID,
    batch: Sequence[ClientEvent],
    now: datetime | None = None,
) -> int:
    """Write a client's batch in one transaction and return how many were written.

    Every event is checked first, and every film must exist: one bad event rejects the
    batch (EventRejected) before anything is added.
    """
    now = now or datetime.now(UTC)
    if not batch:
        raise EventRejected("an empty batch")
    if len(batch) > MAX_BATCH:
        raise EventRejected(f"more than {MAX_BATCH} events in one batch")
    for event in batch:
        check(event, now)
    films = {e.movie_id for e in batch if e.movie_id is not None}
    if films:
        found = set((await session.scalars(select(Movie.id).where(Movie.id.in_(films)))).all())
        missing = sorted(films - found)
        if missing:
            raise EventRejected(f"films not in the catalogue: {missing}")
    for event in batch:
        add(
            session,
            user_id,
            event.type,  # type: ignore[arg-type]  # checked against CLIENT_EVENT_TYPES
            movie_id=event.movie_id,
            source=event.source,  # type: ignore[arg-type]  # checked against SOURCES
            props=event.props,
            at=event.at,
        )
    await session.commit()
    return len(batch)
