"""The shared trait contract.

packages/shared/traits.json is the single source of truth for the Movie DNA
vector. Python reads it at import time; the web client keeps its own copy of
the key list. If the two ever disagree, stored vectors are silently
misinterpreted — every score lands on the wrong dimension — and nothing else
in the system would notice. These tests are the thing that notices.
"""

import json
from pathlib import Path

import pytest

from app.traits import TRAIT_COUNT, TRAIT_KEYS

SHARED_SPEC = Path(__file__).resolve().parents[3] / "packages" / "shared" / "traits.json"


@pytest.fixture(scope="module")
def spec() -> dict:
    return json.loads(SHARED_SPEC.read_text(encoding="utf-8"))


def test_shared_spec_exists() -> None:
    assert SHARED_SPEC.is_file(), f"shared trait spec not found at {SHARED_SPEC}"


def test_keys_match_exactly_and_in_order(spec: dict) -> None:
    json_keys = tuple(d["key"] for d in spec["dimensions"])
    assert json_keys == TRAIT_KEYS, (
        f"traits.json and app.traits.TRAIT_KEYS disagree. JSON: {json_keys}\nPython: {TRAIT_KEYS}"
    )


def test_count_matches(spec: dict) -> None:
    assert len(spec["dimensions"]) == TRAIT_COUNT


def test_keys_are_unique(spec: dict) -> None:
    keys = [d["key"] for d in spec["dimensions"]]
    assert len(keys) == len(set(keys)), "duplicate trait key in traits.json"


def test_every_dimension_is_fully_described(spec: dict) -> None:
    for dimension in spec["dimensions"]:
        for field in ("key", "label_en", "label_uz", "description"):
            assert dimension.get(field), f"{dimension.get('key')} is missing {field}"


def test_scale_is_zero_to_hundred(spec: dict) -> None:
    assert spec["scale"] == {"min": 0, "max": 100}
