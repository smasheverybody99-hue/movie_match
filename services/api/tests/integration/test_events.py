"""Events (Phase 5): every type is recorded with the right shape, a batch is one
transaction, and a malformed batch is rejected whole - never partly written."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event
from app.services import assistant as assistant_service
from app.services import events
from app.services.events import ClientEvent
from app.services.users import ensure_user
from tests.integration.api import api_client, auth, seed_films

A, B = 9_810_001, 9_810_002


@pytest.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed_films(db_session, {A: [60.0] * 14, B: None})
    return db_session


async def _events(session: AsyncSession, user_id: uuid.UUID) -> list[Event]:
    session.expire_all()
    rows = await session.scalars(select(Event).where(Event.user_id == user_id).order_by(Event.id))
    return list(rows.all())


def _shape(event: Event) -> tuple:
    return (event.type, event.movie_id, event.source, event.props)


def _now() -> str:
    return datetime.now(UTC).isoformat()


# --- the client's events ------------------------------------------------------------


async def test_a_batch_records_each_client_type_with_its_shape(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    at = datetime.now(UTC) - timedelta(minutes=3)
    batch = [
        {"type": "recommendation_shown", "at": at.isoformat(), "movie_id": A, "source": "for_you"},
        {"type": "recommendation_clicked", "at": _now(), "movie_id": A, "source": "for_you"},
        {"type": "recommendation_shown", "at": _now(), "movie_id": B, "source": "assistant"},
        {"type": "onboarding_step", "at": _now(), "step": "pick"},
    ]
    async with api_client(seeded) as client:
        response = await client.post("/events", json={"events": batch}, headers=auth(me))
    assert response.status_code == 200, response.text
    assert response.json() == {"recorded": 4}
    stored = await _events(seeded, me)
    assert [_shape(e) for e in stored] == [
        ("recommendation_shown", A, "for_you", {}),
        ("recommendation_clicked", A, "for_you", {}),
        ("recommendation_shown", B, "assistant", {}),
        ("onboarding_step", None, None, {"step": "pick"}),
    ]
    # The client's time is kept; the server's arrival time is separate.
    assert abs((stored[0].occurred_at - at).total_seconds()) < 0.001
    assert all(e.received_at is not None for e in stored)


async def test_a_batch_is_one_transaction(seeded: AsyncSession) -> None:
    """Five events, one commit."""
    me = uuid.uuid4()
    await ensure_user(seeded, me)
    batch = [ClientEvent("recommendation_shown", datetime.now(UTC), A, "under_90")] * 5
    commits = 0
    original = seeded.commit

    async def counting() -> None:
        nonlocal commits
        commits += 1
        await original()

    seeded.commit = counting  # type: ignore[method-assign]
    try:
        recorded = await events.record_batch(seeded, me, batch)
    finally:
        seeded.commit = original  # type: ignore[method-assign]
    assert (recorded, commits) == (5, 1)
    assert len(await _events(seeded, me)) == 5


@pytest.mark.parametrize(
    "bad",
    [
        {"type": "rated", "movie_id": A},  # the server's own event
        {"type": "recommendation_shown", "movie_id": A},  # no source
        {"type": "recommendation_shown", "movie_id": A, "source": "search"},  # unknown source
        {"type": "recommendation_shown", "source": "for_you"},  # no film
        {"type": "onboarding_step"},  # no step
        {"type": "onboarding_step", "step": "pick", "movie_id": A},  # a film it cannot have
        {"type": "recommendation_shown", "movie_id": A, "source": "for_you", "text": "hi"},
        {"type": "recommendation_shown", "movie_id": 999_999_998, "source": "for_you"},
    ],
)
async def test_one_malformed_event_rejects_the_whole_batch(seeded: AsyncSession, bad: dict) -> None:
    me = uuid.uuid4()
    good = {"type": "recommendation_shown", "at": _now(), "movie_id": A, "source": "for_you"}
    async with api_client(seeded) as client:
        response = await client.post(
            "/events", json={"events": [good, {"at": _now(), **bad}, good]}, headers=auth(me)
        )
    assert response.status_code == 422, response.text
    assert await _events(seeded, me) == []  # not the good ones either


async def test_an_event_from_too_long_ago_is_rejected(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    old = (datetime.now(UTC) - timedelta(days=8)).isoformat()
    event = {"type": "recommendation_shown", "at": old, "movie_id": A, "source": "for_you"}
    async with api_client(seeded) as client:
        response = await client.post("/events", json={"events": [event]}, headers=auth(me))
    assert response.status_code == 422
    assert "too far" in response.json()["detail"]
    assert await _events(seeded, me) == []


@pytest.mark.parametrize(
    "body", [{}, {"events": []}, {"events": "x"}, {"events": [{"type": "shown"}]}]
)
async def test_invalid_bodies_are_422(seeded: AsyncSession, body: dict) -> None:
    async with api_client(seeded) as client:
        response = await client.post("/events", json=body, headers=auth(uuid.uuid4()))
    assert response.status_code == 422


async def test_more_than_fifty_events_are_422(seeded: AsyncSession) -> None:
    event = {"type": "recommendation_shown", "at": _now(), "movie_id": A, "source": "for_you"}
    async with api_client(seeded) as client:
        response = await client.post(
            "/events", json={"events": [event] * 51}, headers=auth(uuid.uuid4())
        )
    assert response.status_code == 422


async def test_missing_and_forged_tokens_are_401(seeded: AsyncSession) -> None:
    event = {"type": "recommendation_shown", "at": _now(), "movie_id": A, "source": "for_you"}
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        missing = await client.post("/events", json={"events": [event]})
        forged = await client.post(
            "/events", json={"events": [event]}, headers=auth(me, forged=True)
        )
    assert (missing.status_code, forged.status_code) == (401, 401)
    assert await _events(seeded, me) == []


# --- the server's events, written with the action -----------------------------------


async def test_the_server_records_rated_watchlist_and_watched(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        await client.post("/ratings", json={"movie_id": A, "score": 8}, headers=auth(me))
        await client.post("/watchlist", json={"movie_id": B}, headers=auth(me))
        await client.post(f"/watchlist/{B}/watched", headers=auth(me))
    assert [_shape(e) for e in await _events(seeded, me)] == [
        ("rated", A, None, {}),
        ("added_to_watchlist", B, None, {}),
        ("marked_watched", B, None, {}),
    ]


async def test_a_failed_action_records_nothing(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        not_listed = await client.post(f"/watchlist/{A}/watched", headers=auth(me))
        no_film = await client.post(
            "/ratings", json={"movie_id": 999_999_997, "score": 8}, headers=auth(me)
        )
    assert (not_listed.status_code, no_film.status_code) == (404, 404)
    assert await _events(seeded, me) == []


async def test_onboarding_done_is_recorded_once(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        first = await client.post("/onboarding/done", headers=auth(me))
        again = await client.post("/onboarding/done", headers=auth(me))
        missing = await client.post("/onboarding/done")
    assert (first.status_code, again.status_code, missing.status_code) == (204, 204, 401)
    assert [_shape(e) for e in await _events(seeded, me)] == [("onboarding_done", None, None, {})]


async def test_an_assistant_message_is_recorded_when_it_is_counted(
    db_session: AsyncSession,
) -> None:
    me = uuid.uuid4()
    await ensure_user(db_session, me)
    noon = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    assert await assistant_service.claim(db_session, me, 1, now=noon) is None
    assert await assistant_service.claim(db_session, me, 1, now=noon) is not None  # refused
    stored = await _events(db_session, me)
    assert [_shape(e) for e in stored] == [("assistant_query", None, None, {})]
    assert stored[0].occurred_at == noon


async def test_events_go_with_the_account(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        await client.post("/ratings", json={"movie_id": A, "score": 8}, headers=auth(me))
        await client.delete("/me", headers=auth(me))
    count = await seeded.scalar(select(func.count()).select_from(Event).where(Event.user_id == me))
    assert count == 0
