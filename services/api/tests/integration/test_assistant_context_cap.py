"""Context is the last five turns, the current message included: the 6th drops the 1st.

Stored turns are capped too, and a new conversation starts with none."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AssistantTurn
from app.services.assistant import CONTEXT_TURNS
from tests.assistant_recorded import recorded_assistant, user_texts
from tests.conftest import requires_db
from tests.integration.api import api_client, auth
from tests.integration.assistant_world import new_viewer

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]


async def _turns(session: AsyncSession, me: object) -> int:
    count = await session.scalar(
        select(func.count()).select_from(AssistantTurn).where(AssistantTurn.user_id == me)
    )
    return count or 0


async def test_the_sixth_turn_drops_the_first_from_context(
    assistant_catalogue: AsyncSession,
) -> None:
    session = assistant_catalogue
    me = await new_viewer(session)
    assistant, sdk = recorded_assistant(*["plain_answer"] * 7)
    async with api_client(session, assistant=assistant) as client:
        for i in range(1, 7):
            response = await client.post(
                "/assistant/chat", json={"message": f"question {i}"}, headers=auth(me)
            )
            assert response.status_code == 200, response.text

        assert CONTEXT_TURNS == 5
        assert user_texts(sdk.requests[4]) == [f"question {i}" for i in range(1, 6)]
        assert user_texts(sdk.requests[5]) == [f"question {i}" for i in range(2, 7)]
        # Earlier answers are in context too, as the model's own turns.
        model_turns = [c for c in sdk.requests[5]["contents"] if c["role"] == "model"]
        assert len(model_turns) == CONTEXT_TURNS - 1
        assert model_turns[0]["parts"][0]["text"].startswith("Tell me a little more")
        assert await _turns(session, me) == CONTEXT_TURNS

        response = await client.post(
            "/assistant/chat",
            json={"message": "fresh start", "new_conversation": True},
            headers=auth(me),
        )
        assert response.status_code == 200, response.text
    assert user_texts(sdk.requests[6]) == ["fresh start"]
    assert await _turns(session, me) == 1
