"""A non-film question takes the refusal path: a `refusal` event, no tool call, no cards.

The recorded answer is the hard case: it marks the message off-topic and, in the same
answer, asks for the tool anyway. The refusal wins and the engine is never reached."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AssistantTurn
from app.services import recommend
from tests.assistant_recorded import card_ids, events, recorded_assistant, text_of
from tests.conftest import requires_db
from tests.integration.api import api_client, auth
from tests.integration.assistant_world import new_viewer

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]


async def test_a_non_film_question_is_refused_without_a_tool_call(
    assistant_catalogue: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = assistant_catalogue
    calls: list[object] = []

    async def search(*args: object, **kwargs: object) -> None:
        calls.append(args)
        raise AssertionError("the engine must not be called for an off-topic message")

    monkeypatch.setattr(recommend, "search", search)
    me = await new_viewer(session)
    assistant, sdk = recorded_assistant("off_topic")
    async with api_client(session, assistant=assistant) as client:
        response = await client.post(
            "/assistant/chat",
            json={"message": "What's the capital of Australia?"},
            headers=auth(me),
        )

    assert response.status_code == 200, response.text
    stream = events(response.text)
    assert ("refusal", {"reason": "off_topic"}) in stream
    assert stream[-1] == ("done", {})
    assert calls == []
    assert len(sdk.requests) == 1  # no second call: nothing to answer after a tool
    assert card_ids(stream) == []
    assert not [name for name, _ in stream if name == "followups"]
    assert "off_topic" not in text_of(stream)

    # The turn is kept as context, with no answer and no films.
    turn = await session.scalar(select(AssistantTurn).where(AssistantTurn.user_id == me))
    assert turn is not None
    assert (turn.answer, turn.movie_ids) == ("", [])
