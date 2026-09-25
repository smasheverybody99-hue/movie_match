"""Model output validation. Anything malformed raises; nothing is filled with defaults."""

import json

import pytest

from app.pipelines.traits import parse_response
from app.traits import TRAIT_KEYS


def _valid(**overrides: object) -> dict:
    data: dict = {key: 50 + i for i, key in enumerate(TRAIT_KEYS)}
    data["summary"] = "For viewers who like slow, careful films."
    data.update(overrides)
    return data


def test_valid_response_parses() -> None:
    parsed = parse_response(json.dumps(_valid()))
    assert list(parsed["scores"]) == list(TRAIT_KEYS)
    assert parsed["scores"]["psychological_complexity"] == 50.0
    assert parsed["scores"]["ending_ambiguity"] == 63.0
    assert parsed["summary"] == "For viewers who like slow, careful films."


def test_boundaries_are_inclusive() -> None:
    parsed = parse_response(json.dumps(_valid(humor=0, violence=100)))
    assert parsed["scores"]["humor"] == 0.0
    assert parsed["scores"]["violence"] == 100.0


def test_missing_key_raises() -> None:
    data = _valid()
    del data["darkness"]
    with pytest.raises(ValueError, match="missing trait: darkness"):
        parse_response(json.dumps(data))


@pytest.mark.parametrize("value", [-1, 101, 250.5])
def test_out_of_range_raises(value: float) -> None:
    with pytest.raises(ValueError, match="out of range"):
        parse_response(json.dumps(_valid(pacing=value)))


def test_nan_raises() -> None:
    text = json.dumps(_valid()).replace('"pacing": 55', '"pacing": NaN')
    with pytest.raises(ValueError):
        parse_response(text)


def test_extra_keys_are_ignored() -> None:
    parsed = parse_response(json.dumps(_valid(confidence=0.9, genre="drama")))
    assert set(parsed["scores"]) == set(TRAIT_KEYS)


@pytest.mark.parametrize("text", ["", "Sure! Here are the scores.", "{not json}", "[1, 2, 3]"])
def test_non_json_or_non_object_raises(text: str) -> None:
    with pytest.raises(ValueError):
        parse_response(text)


@pytest.mark.parametrize("value", ["80", True, None, [80]])
def test_non_numeric_score_raises(value: object) -> None:
    """A string "80" or a boolean is a malformed answer, not a score to coerce."""
    with pytest.raises(ValueError, match="not a number"):
        parse_response(json.dumps(_valid(romance=value)))


def test_json_fence_is_tolerated() -> None:
    text = "```json\n" + json.dumps(_valid()) + "\n```"
    assert parse_response(text)["scores"]["pacing"] == 55.0


def test_empty_summary_becomes_none() -> None:
    assert parse_response(json.dumps(_valid(summary="  ")))["summary"] is None
    data = _valid()
    del data["summary"]
    assert parse_response(json.dumps(data))["summary"] is None
