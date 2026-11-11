"""assistant_daily_calls_per_user: N messages a UTC day, the N+1st is a 429 with the reset
time, and the model is not called for it."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import assistant as service
from app.services.users import ensure_user
from tests.assistant_recorded import recorded_assistant
from tests.conftest import requires_db
from tests.integration.api import api_client, auth
from tests.integration.assistant_world import new_viewer

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]

CAP = 3


async def test_the_message_after_the_cap_is_429_with_the_reset_time(
    assistant_catalogue: AsyncSession,
) -> None:
    session = assistant_catalogue
    me = await new_viewer(session)
    assistant, sdk = recorded_assistant(*["plain_answer"] * (CAP + 1))
    settings = {"assistant_daily_calls_per_user": CAP}
    async with api_client(session, assistant=assistant, settings=settings) as client:
        answers = [
            await client.post("/assistant/chat", json={"message": f"hi {i}"}, headers=auth(me))
            for i in range(CAP + 1)
        ]

    assert [r.status_code for r in answers[:CAP]] == [200] * CAP
    last = answers[CAP]
    assert last.status_code == 429
    body = last.json()
    assert body["limit"] == CAP
    assert body["detail"]
    resets = datetime.fromisoformat(body["resets_at"])
    now = datetime.now(UTC)
    assert resets == service.resets_at(now) or resets == service.resets_at(now - timedelta(1))
    assert (resets.hour, resets.minute, resets.second) == (0, 0, 0)
    assert resets.utcoffset() == timedelta(0)
    assert 0 < int(last.headers["Retry-After"]) <= 24 * 3600
    assert len(sdk.requests) == CAP  # the refused message never reached the model


async def test_the_cap_is_per_user_and_per_utc_day(assistant_catalogue: AsyncSession) -> None:
    session = assistant_catalogue
    me, other = uuid.uuid4(), uuid.uuid4()
    await ensure_user(session, me)  # assistant_usage has a foreign key to users
    await ensure_user(session, other)
    noon = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)

    assert await service.claim(session, me, 2, now=noon) is None
    assert await service.claim(session, me, 2, now=noon) is None
    refused = await service.claim(session, me, 2, now=noon)
    assert refused == datetime(2026, 11, 12, tzinfo=UTC)
    # A refusal is not counted: still refused, and the next day starts again from zero.
    assert await service.claim(session, me, 2, now=noon) == refused
    assert await service.claim(session, other, 2, now=noon) is None
    assert await service.claim(session, me, 2, now=noon + timedelta(hours=12)) is None
    # A cap of zero refuses everything.
    assert await service.claim(session, other, 0, now=noon) == refused
