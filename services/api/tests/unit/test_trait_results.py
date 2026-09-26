"""Reading one batch result: text to parse, or the reason there is none. No DB, no network.

Results are built through the SDK's own InlinedResponse, which forbids unknown fields.
"""

import json
from typing import Any

import pytest
from google.genai import types

from app.pipelines.traits import read_item
from tests.conftest import load_fixture


def _item(**overrides: Any) -> types.InlinedResponse:
    base: dict[str, Any] = {"metadata": {"key": "movie-1"}}
    return types.InlinedResponse.model_validate({**base, **overrides})


def _answer(parts: list[dict], finish: str | None = "STOP") -> dict:
    candidate: dict[str, Any] = {"content": {"role": "model", "parts": parts}}
    if finish:
        candidate["finishReason"] = finish
    return {"response": {"candidates": [candidate]}}


def test_recorded_fixture_items_read_as_expected() -> None:
    valid, malformed, truncated, errored = (
        types.InlinedResponse.model_validate(i) for i in load_fixture("gemini_batch_results.json")
    )
    text, error = read_item(valid)
    assert error is None and text is not None
    assert json.loads(text)["plot_twist"] == 95
    assert read_item(malformed)[1] is None  # readable; parse_response is what rejects it
    assert read_item(truncated) == (None, "truncated at max_tokens")
    text, error = read_item(errored)
    assert (
        text is None
        and error == "batch result errored: The model is overloaded. Please try again later."
    )


def test_text_parts_are_joined() -> None:
    item = _item(**_answer([{"text": '{"a": '}, {"text": "1}"}]))
    assert read_item(item) == ('{"a": 1}', None)


def test_thinking_parts_are_not_part_of_the_answer() -> None:
    item = _item(**_answer([{"text": "let me think", "thought": True}, {"text": "{}"}]))
    assert read_item(item) == ("{}", None)


def test_missing_finish_reason_is_read_as_a_clean_stop() -> None:
    assert read_item(_item(**_answer([{"text": "{}"}], finish=None))) == ("{}", None)


@pytest.mark.parametrize("reason", ["SAFETY", "PROHIBITED_CONTENT", "RECITATION", "OTHER"])
def test_a_refused_answer_is_a_failure_not_text(reason: str) -> None:
    item = _item(**_answer([{"text": "partial"}], finish=reason))
    assert read_item(item) == (None, f"finish_reason {reason}")


def test_a_blocked_prompt_says_why() -> None:
    item = _item(response={"promptFeedback": {"blockReason": "PROHIBITED_CONTENT"}})
    text, error = read_item(item)
    assert text is None
    assert error is not None and error.startswith("no candidates (prompt blocked:")
    assert "PROHIBITED_CONTENT" in error


def test_no_candidates_and_no_reason() -> None:
    assert read_item(_item(response={"candidates": []})) == (None, "no candidates")
    assert read_item(_item()) == (None, "no candidates")


def test_an_answer_without_text_reads_as_empty_text() -> None:
    """Empty text goes on to parse_response, which rejects it as not JSON."""
    item = _item(**_answer([]))
    assert read_item(item) == ("", None)


def test_error_without_message_falls_back_to_the_code() -> None:
    item = _item(error={"code": 500})
    assert read_item(item) == (None, "batch result errored: 500")
