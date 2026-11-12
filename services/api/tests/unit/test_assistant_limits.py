"""The time limits of one message (FR-8, ADR 0009 amendment 2026-11-13), on a scripted
provider: no network, and the limits shrunk to fractions of a second.

Measured 2026-11-12: the first words came at 15-39 s, one answer stalled after its first
words until the old 30 s per-call limit, and one message took 52 s to fail. Now the first
words must come within FIRST_TEXT_SECONDS and the end within TOTAL_SECONDS; a stream that
stalls is tried again like a 503; a call the limit cuts off is billed, so its tokens are
estimated."""

import asyncio
from collections.abc import AsyncIterator, Sequence
from typing import Any

import pytest

from app.providers.base import (
    ChatMessage,
    Pricing,
    StreamEnd,
    TextDelta,
    ToolCall,
    ToolRequested,
    ToolSpec,
    TransientError,
    Usage,
)
from app.services import assistant as service
from app.services.assistant import (
    TOOL,
    AnswerFilter,
    Limits,
    OutOfTime,
    Reset,
    Text,
    _Call,
    _call,
    estimated_usage,
)

SCALE = 0.02  # test seconds per production second


@pytest.fixture(autouse=True)
def short_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("FIRST_TEXT_SECONDS", "TOTAL_SECONDS", "STALL_SECONDS", "MIN_TRY_SECONDS"):
        monkeypatch.setattr(service, name, getattr(service, name) * SCALE)
    monkeypatch.setattr(service, "RETRY_DELAY_SECONDS", 0.0)


def wait(seconds: float) -> float:
    """A pause of `seconds` production seconds, as a script step."""
    return seconds * SCALE


class Scripted:
    """A provider whose every call plays the next script: events, pauses (floats) and an
    error, raised after a StreamEnd("interrupted") as the real provider does."""

    provider = "fake"
    model = "fake"
    pricing = Pricing(0.0, 0.0, "test")

    def __init__(self, *scripts: list[Any]) -> None:
        self.scripts = list(scripts)
        self.calls = 0

    async def stream(
        self,
        system: str,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolSpec],
        *,
        allow_tools: bool,
    ) -> AsyncIterator[Any]:
        script = self.scripts[self.calls]
        self.calls += 1
        for step in script:
            if isinstance(step, float):
                await asyncio.sleep(step)
            elif isinstance(step, Exception):
                yield StreamEnd(Usage(requests=1, input_tokens=100), stop="interrupted")
                raise step
            else:
                yield step


def ended(input_tokens: int = 100) -> StreamEnd:
    return StreamEnd(Usage(requests=1, input_tokens=input_tokens, output_tokens=10))


MESSAGES = [ChatMessage("user", "Something calm")]


async def run(provider: Scripted, call: _Call, limits: Limits | None = None) -> list[Any]:
    limits = limits or Limits()
    out: list[Any] = []
    async for event in _call(
        provider, "system", MESSAGES, AnswerFilter(), call, [], limits, allow_tools=False
    ):
        if isinstance(event, Text):
            limits.texted = True
        out.append(event)
    return out


async def test_a_stream_that_stalls_after_its_first_words_is_tried_again_behind_a_reset() -> None:
    provider = Scripted(
        [TextDelta("Two short ones. "), wait(15), TextDelta("never shown")],
        [TextDelta("Two short ones. "), TextDelta("[[ask:Shorter]]"), ended()],
    )
    call = _Call()

    out = await run(provider, call)

    assert provider.calls == 2
    assert [type(e).__name__ for e in out] == ["Text", "Reset", "Text"]
    assert call.retries == 1 and call.estimated == 1
    # The cut-off attempt is estimated (the provider never counted it), the retry reported.
    assert call.usage.requests == 2 and call.usage.estimated
    assert call.usage.input_tokens > 100 and call.usage.output_tokens > 10


async def test_no_words_within_the_first_limit_ends_the_message_and_bills_the_attempt() -> None:
    provider = Scripted([wait(30), TextDelta("too late"), ended()])
    call = _Call()

    with pytest.raises(OutOfTime):
        await run(provider, call)

    assert provider.calls == 1  # a wait before anything arrived is not a stall: no retry
    assert call.usage.requests == 1 and call.usage.estimated
    assert call.usage.output_tokens == 0


async def test_a_slow_first_answer_is_not_cut_off_before_the_first_limit() -> None:
    # 2026-11-12: a call that only asks for the tool sent nothing for up to 19 s and was
    # fine. Waiting longer than STALL_SECONDS before the first event is allowed.
    provider = Scripted([wait(15), ToolRequested(ToolCall(TOOL.name, {})), ended()])
    call = _Call()

    assert await run(provider, call) == []
    assert call.tool_call is not None and call.retries == 0 and not call.usage.estimated


async def test_once_words_are_shown_only_the_total_limit_applies() -> None:
    limits = Limits()
    limits.texted = True
    provider = Scripted([wait(30), TextDelta("in time"), ended()])

    out = await run(provider, _Call(), limits)

    assert out == [Text("in time")]


async def test_the_total_limit_ends_an_answer_that_keeps_trickling() -> None:
    steps: list[Any] = []
    for _ in range(12):
        steps += [TextDelta("more "), wait(5)]  # never a stall, but 60 s in all
    provider = Scripted([*steps, ended()])
    call = _Call()

    with pytest.raises(OutOfTime):
        await run(provider, call)
    assert provider.calls == 1 and call.usage.estimated


async def test_no_retry_is_made_without_time_left_for_it() -> None:
    provider = Scripted(
        [wait(21), TransientError("503 UNAVAILABLE")],
        [TextDelta("never asked"), ended()],
    )
    call = _Call()

    with pytest.raises(OutOfTime):
        await run(provider, call)
    assert provider.calls == 1
    assert not call.usage.estimated  # the provider reported the 503 attempt itself


async def test_a_limit_reached_after_the_follow_ups_keeps_the_complete_answer() -> None:
    provider = Scripted([TextDelta("Done. [[ask:Shorter]]"), wait(50), ended()])
    call = _Call()

    out = await run(provider, call)

    assert out == [Text("Done. ")]
    assert call.broke_off and call.stop == "done"


async def test_a_reset_is_sent_only_when_the_broken_attempt_had_shown_something() -> None:
    provider = Scripted([TransientError("503")], [TextDelta("Hi"), ended()])
    out = await run(provider, _Call())
    assert Reset() not in out and out == [Text("Hi")]


def test_an_estimate_counts_what_was_sent_and_received_in_characters() -> None:
    call = ToolCall(TOOL.name, {"mood": "calm"})
    messages = [
        ChatMessage("user", "x" * 700),
        ChatMessage("assistant", tool_call=call),
        ChatMessage("tool", tool_call=call, result={"films": []}),
    ]
    bare = estimated_usage("", [], 0).input_tokens  # the tool schema alone
    usage = estimated_usage("s" * 350, messages, 35)

    assert usage.estimated and usage.requests == 1
    assert usage.input_tokens >= bare + (350 + 700) / service.CHARS_PER_TOKEN
    assert usage.output_tokens == 10
