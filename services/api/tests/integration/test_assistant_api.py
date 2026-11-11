"""POST /assistant/chat: the cases every endpoint has (CLAUDE.md) and the provider's
failures once the stream has started."""

import uuid
from collections.abc import AsyncIterator, Sequence

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.base import (
    AssistantEvent,
    ChatMessage,
    Pricing,
    StreamEnd,
    TextDelta,
    ToolSpec,
    TransientError,
    Usage,
)
from tests.assistant_recorded import events, recorded_assistant
from tests.conftest import requires_db
from tests.integration.api import api_client, auth
from tests.integration.assistant_world import new_viewer

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]

URL = "/assistant/chat"
BODY = {"message": "Something funny"}


async def test_missing_auth_is_401(assistant_catalogue: AsyncSession) -> None:
    assistant, sdk = recorded_assistant("plain_answer")
    async with api_client(assistant_catalogue, assistant=assistant) as client:
        response = await client.post(URL, json=BODY)
    assert response.status_code == 401
    assert sdk.requests == []


async def test_a_forged_token_is_401(assistant_catalogue: AsyncSession) -> None:
    assistant, sdk = recorded_assistant("plain_answer")
    async with api_client(assistant_catalogue, assistant=assistant) as client:
        response = await client.post(URL, json=BODY, headers=auth(uuid.uuid4(), forged=True))
    assert response.status_code == 401
    assert sdk.requests == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 501},
        {"message": "hi", "lang": "de"},
        {"message": 5},
    ],
)
async def test_invalid_input_is_422(assistant_catalogue: AsyncSession, body: dict) -> None:
    me = await new_viewer(assistant_catalogue)
    assistant, sdk = recorded_assistant("plain_answer")
    async with api_client(assistant_catalogue, assistant=assistant) as client:
        response = await client.post(URL, json=body, headers=auth(me))
    assert response.status_code == 422
    assert sdk.requests == []


async def test_not_found(assistant_catalogue: AsyncSession) -> None:
    """The endpoint names no resource, so not-found is the route itself: a wrong path is
    404 and a wrong method 405, neither reaching the model."""
    me = await new_viewer(assistant_catalogue)
    assistant, sdk = recorded_assistant("plain_answer")
    async with api_client(assistant_catalogue, assistant=assistant) as client:
        assert (
            await client.post("/assistant/talk", json=BODY, headers=auth(me))
        ).status_code == 404
        assert (await client.get(URL, headers=auth(me))).status_code == 405
    assert sdk.requests == []


async def test_without_a_provider_key_it_is_503_and_nothing_is_counted(
    assistant_catalogue: AsyncSession,
) -> None:
    me = await new_viewer(assistant_catalogue)
    settings = {"assistant_daily_calls_per_user": 1}
    async with api_client(assistant_catalogue, assistant=None, settings=settings) as client:
        assert (await client.post(URL, json=BODY, headers=auth(me))).status_code == 503
    assistant, _ = recorded_assistant("plain_answer")
    async with api_client(assistant_catalogue, assistant=assistant, settings=settings) as client:
        assert (await client.post(URL, json=BODY, headers=auth(me))).status_code == 200


class Breaks:
    """Says a few words, then the provider fails."""

    provider, model = "fake", "fake-chat"
    pricing = Pricing(1.0, 2.0, "test rates")

    async def stream(
        self,
        system: str,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolSpec],
        *,
        allow_tools: bool,
    ) -> AsyncIterator[AssistantEvent]:
        yield TextDelta("Let me look")
        raise TransientError("503 UNAVAILABLE")


class Blocked(Breaks):
    """The provider's safety filter stops the answer."""

    async def stream(
        self,
        system: str,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolSpec],
        *,
        allow_tools: bool,
    ) -> AsyncIterator[AssistantEvent]:
        yield StreamEnd(Usage(requests=1, input_tokens=10), stop="blocked")


@pytest.mark.parametrize(("model", "reason"), [(Breaks(), "failed"), (Blocked(), "blocked")])
async def test_a_failure_after_the_stream_started_ends_it_with_an_error_event(
    assistant_catalogue: AsyncSession, model: object, reason: str
) -> None:
    me = await new_viewer(assistant_catalogue)
    async with api_client(assistant_catalogue, assistant=model) as client:
        response = await client.post(URL, json=BODY, headers=auth(me))
    assert response.status_code == 200
    stream = events(response.text)
    assert stream[-1] == ("error", {"reason": reason})
    assert ("done", {}) not in stream
