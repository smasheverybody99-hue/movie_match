"""A 503 from the model is tried once more (2026-11-11: five answers in 72 broke off).

Before anything is shown, the retry is invisible. After the answer started, a `reset`
event tells the client to drop it and the retry streams in its place. A second 503 ends
with the error. A break after the follow-ups loses nothing, so the answer stands."""

import logging

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AssistantTurn
from app.services import assistant as service
from tests.assistant_recorded import card_ids, events, recorded_assistant, text_of
from tests.conftest import requires_db
from tests.integration.api import api_client, auth
from tests.integration.assistant_world import new_viewer

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]

ANSWER = "Two short ones that keep you guessing. This one turns on what its hero believes."


@pytest.fixture(autouse=True)
def no_wait(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(service, "RETRY_DELAY_SECONDS", 0.0)
    caplog.set_level(logging.INFO, logger="app.services.assistant")
    caplog.set_level(logging.INFO, logger="app.cost")


async def _ask(session: AsyncSession, *fixtures: str):  # type: ignore[no-untyped-def]
    me = await new_viewer(session)
    assistant, sdk = recorded_assistant(*fixtures)
    async with api_client(session, assistant=assistant) as client:
        response = await client.post(
            "/assistant/chat", json={"message": "Something short"}, headers=auth(me)
        )
    assert response.status_code == 200, response.text
    turn = await session.scalar(select(AssistantTurn).where(AssistantTurn.user_id == me))
    return events(response.text), sdk, turn


def _after_reset(stream: list) -> list:
    names = [name for name, _ in stream]
    return stream[len(names) - names[::-1].index("reset") :]


def _line(caplog: pytest.LogCaptureFixture, start: str) -> str:
    return next(r.getMessage() for r in caplog.records if r.getMessage().startswith(start))


async def test_a_503_before_anything_is_shown_is_tried_again_unseen(
    assistant_catalogue: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    stream, sdk, turn = await _ask(assistant_catalogue, "unavailable", "tool_call")

    assert len(sdk.requests) == 3  # the 503, the same call again, the answer
    assert sdk.requests[0]["contents"] == sdk.requests[1]["contents"]
    assert "reset" not in [name for name, _ in stream]
    assert text_of(stream).startswith(ANSWER)
    assert card_ids(stream)[:2] == [9_600_001, 9_600_002]
    assert stream[-1] == ("done", {})
    assert turn is not None
    assert "retries=1 end=done" in _line(caplog, "assistant timing")


async def test_a_503_in_the_middle_of_the_answer_resets_it_and_the_retry_takes_its_place(
    assistant_catalogue: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    stream, sdk, turn = await _ask(
        assistant_catalogue, "tool_call#1", "broken_answer", "tool_call#2"
    )

    names = [name for name, _ in stream]
    assert names.count("reset") == 1
    before = stream[: names.index("reset")]
    assert card_ids(before) == [9_600_001]  # what the broken attempt had shown
    after = _after_reset(stream)
    assert text_of(after).startswith(ANSWER)
    assert card_ids(after)[:2] == [9_600_001, 9_600_002]  # shown again, not dropped as repeats
    assert after[-1] == ("done", {})
    assert len(sdk.requests) == 3
    assert sdk.requests[1]["contents"] == sdk.requests[2]["contents"]
    # The context keeps the answer once, not the broken start as well.
    assert turn is not None and turn.answer.count("Two short ones") == 1
    assert "retries=1 end=done" in _line(caplog, "assistant timing")


async def test_a_second_503_ends_with_the_error_and_both_attempts_are_counted(
    assistant_catalogue: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    stream, sdk, turn = await _ask(
        assistant_catalogue, "tool_call#1", "broken_answer", "broken_answer"
    )

    assert [name for name, _ in stream].count("reset") == 1
    assert stream[-1] == ("error", {"reason": "failed"})
    assert ("done", {}) not in stream
    assert len(sdk.requests) == 3
    assert turn is None  # a failed answer is not kept as context
    cost = _line(caplog, "run=assistant")
    # The tool call (1,850 in, 54 out) and two broken answers (2,400 in, 20 out each).
    assert "requests=3 input_tokens=6650 output_tokens=94" in cost
    assert "status=interrupted" in cost


async def test_a_break_after_the_follow_ups_keeps_the_complete_answer(
    assistant_catalogue: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    stream, sdk, turn = await _ask(assistant_catalogue, "tool_call#1", "answer_then_break")

    names = [name for name, _ in stream]
    assert "reset" not in names and "error" not in names
    assert card_ids(stream)[:2] == [9_600_001, 9_600_002]
    followups = [data["items"] for name, data in stream if name == "followups"]
    assert followups == [["Something even shorter", "Older films like these"]]
    assert stream[-1] == ("done", {})
    assert len(sdk.requests) == 2  # nothing was lost, so nothing is asked again
    assert turn is not None
    assert "status=interrupted" in _line(caplog, "run=assistant")
