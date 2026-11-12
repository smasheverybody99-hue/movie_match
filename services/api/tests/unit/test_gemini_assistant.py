"""GeminiAssistant on recorded stream chunks: events, the call sent back, usage, errors."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from google.genai import errors, types

from app.config import Settings
from app.providers.base import (
    ChatMessage,
    ProviderUnavailable,
    RateLimited,
    StreamEnd,
    TextDelta,
    ToolCall,
    ToolRequested,
    TransientError,
    Usage,
)
from app.providers.gemini import ASSISTANT_PRICING, GeminiAssistant, GeminiProvider, chat_contents
from app.services.assistant import TOOL
from tests.assistant_recorded import RecordedSdk, recorded_assistant


async def collect(assistant: Any, messages: list[ChatMessage], allow_tools: bool = True) -> list:
    return [e async for e in assistant.stream("sys", messages, [TOOL], allow_tools=allow_tools)]


async def test_a_function_call_comes_after_the_text_with_its_own_parts() -> None:
    assistant, sdk = recorded_assistant("tool_call")
    out = await collect(assistant, [ChatMessage("user", "90 minutes")])
    (requested, end) = out
    assert isinstance(requested, ToolRequested)
    assert requested.call.name == "search_movies"
    assert requested.call.args["runtime_max"] == 90
    assert requested.call.raw[0].thought_signature == b"signature-1"
    assert end == StreamEnd(Usage(1, 1850, 54), "done")
    assert sdk.requests[0]["config"]["system_instruction"] == "sys"
    assert sdk.requests[0]["contents"] == [{"role": "user", "parts": [{"text": "90 minutes"}]}]


async def test_text_streams_in_order_and_cached_tokens_are_reported() -> None:
    sdk = RecordedSdk("tool_call")
    sdk.calls = sdk.calls[1:]  # only the answer after the tool
    out = await collect(GeminiAssistant(sdk), [ChatMessage("user", "x")], allow_tools=False)
    deltas = [e.text for e in out if isinstance(e, TextDelta)]
    assert len(deltas) == 3
    assert "".join(deltas).startswith("Two short ones")
    end = out[-1]
    assert end.usage == Usage(1, 2400, 70, cached_input_tokens=1800)
    # 600 uncached at 0.30, 1,800 cached at 0.03, 70 out at 2.50 (per million).
    assert ASSISTANT_PRICING.usd(end.usage) == pytest.approx(
        (600 * 0.30 + 1800 * 0.03 + 70 * 2.5) / 1e6
    )


def test_a_call_and_its_result_go_back_as_gemini_contents() -> None:
    call = ToolCall("search_movies", {"mood": "funny"})
    contents = chat_contents(
        [
            ChatMessage("user", "hi"),
            ChatMessage("assistant", "Hello"),
            ChatMessage("assistant", tool_call=call),
            ChatMessage("tool", tool_call=call, result={"films": []}),
        ]
    )
    assert contents == [
        {"role": "user", "parts": [{"text": "hi"}]},
        {"role": "model", "parts": [{"text": "Hello"}]},
        {
            "role": "model",
            "parts": [{"function_call": {"name": "search_movies", "args": {"mood": "funny"}}}],
        },
        {
            "role": "user",
            "parts": [{"function_response": {"name": "search_movies", "response": {"films": []}}}],
        },
    ]


class Chunks:
    """A fake SDK that plays raw chunk dicts, or raises."""

    def __init__(self, chunks: list[dict] | None = None, error: Exception | None = None) -> None:
        self.chunks, self.error = chunks or [], error

    @property
    def models(self) -> "Chunks":
        return self

    async def generate_content_stream(self, **_: Any) -> AsyncIterator[Any]:
        if self.error:
            raise self.error

        async def play() -> AsyncIterator[Any]:
            for chunk in self.chunks:
                yield types.GenerateContentResponse.model_validate(chunk)

        return play()


def _ended(reason: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": "a"}]}, "finishReason": reason}]}


@pytest.mark.parametrize(
    ("chunk", "stop", "shown"),
    [
        (_ended("SAFETY"), "blocked", ["a"]),
        (_ended("MAX_TOKENS"), "truncated", ["a"]),
        (_ended("MALFORMED_FUNCTION_CALL"), "blocked", ["a"]),
        ({"promptFeedback": {"blockReason": "SAFETY"}}, "blocked", []),
        # A thought part is the model's reasoning: never shown.
        ({"candidates": [{"content": {"parts": [{"text": "a", "thought": True}]}}]}, "done", []),
    ],
)
async def test_how_the_answer_ended(chunk: dict, stop: str, shown: list[str]) -> None:
    out = await collect(GeminiAssistant(Chunks([chunk])), [ChatMessage("user", "x")])
    assert out[-1].stop == stop
    assert [e.text for e in out if isinstance(e, TextDelta)] == shown


@pytest.mark.parametrize(
    ("code", "status", "neutral"),
    [
        (429, "RESOURCE_EXHAUSTED", RateLimited),
        (503, "UNAVAILABLE", TransientError),
        (403, "PERMISSION_DENIED", ProviderUnavailable),
    ],
)
async def test_api_errors_become_the_neutral_ones(code: int, status: str, neutral: type) -> None:
    error = errors.APIError(code, {"error": {"code": code, "status": status, "message": "no"}})
    with pytest.raises(neutral):
        await collect(GeminiAssistant(Chunks(error=error)), [ChatMessage("user", "x")])


async def test_a_dropped_connection_is_transient() -> None:
    with pytest.raises(TransientError):
        await collect(GeminiAssistant(Chunks(error=TimeoutError())), [ChatMessage("user", "x")])


def test_there_is_no_assistant_without_a_key() -> None:
    assert GeminiProvider(Settings(_env_file=None)).assistant() is None
    with_key = GeminiProvider(Settings(_env_file=None, gemini_api_key="k")).assistant()
    assert with_key is not None and with_key.model == "gemini-3.5-flash-lite"


async def test_a_503_in_the_middle_still_counts_the_tokens_then_raises() -> None:
    assistant, _ = recorded_assistant("broken_answer")
    seen: list = []
    with pytest.raises(TransientError, match="503"):
        async for event in assistant.stream(
            "sys", [ChatMessage("user", "x")], [TOOL], allow_tools=False
        ):
            seen.append(event)
    assert [e.text for e in seen if isinstance(e, TextDelta)] == [
        "Two short ones that keep you guessing. [[film:9600001]] This one"
    ]
    # The usage so far comes before the error, so the cost line can count it.
    assert seen[-1] == StreamEnd(Usage(1, 2400, 20), "interrupted", "503 UNAVAILABLE")


async def test_a_503_before_the_first_chunk_counts_one_request() -> None:
    assistant, _ = recorded_assistant("unavailable")
    seen: list = []
    with pytest.raises(TransientError):
        async for event in assistant.stream(
            "sys", [ChatMessage("user", "x")], [TOOL], allow_tools=True
        ):
            seen.append(event)
    assert seen == [StreamEnd(Usage(requests=1), "interrupted", "503 UNAVAILABLE")]


@pytest.mark.parametrize(
    ("chunk", "detail"),
    [
        (
            {
                "candidates": [
                    {
                        "content": {"parts": [{"text": "a"}]},
                        "finishReason": "RECITATION",
                        "safetyRatings": [
                            {"category": "HARM_CATEGORY_HARASSMENT", "probability": "NEGLIGIBLE"},
                            {
                                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                "probability": "MEDIUM",
                                "blocked": True,
                            },
                        ],
                    }
                ]
            },
            "finish_reason=RECITATION safety=HARM_CATEGORY_DANGEROUS_CONTENT:MEDIUM:blocked",
        ),
        (_ended("SAFETY"), "finish_reason=SAFETY"),
        ({"promptFeedback": {"blockReason": "OTHER"}}, "block_reason=OTHER"),
        (
            {"candidates": [{"content": {"parts": [{"text": "a"}]}, "finishReason": "STOP"}]},
            "",
        ),
    ],
)
async def test_an_answer_that_did_not_end_cleanly_says_why(chunk: dict, detail: str) -> None:
    """2026-11-11: one answer ended "blocked" and the log could not say why."""
    out = await collect(GeminiAssistant(Chunks([chunk])), [ChatMessage("user", "x")])
    assert out[-1].detail == detail
