"""The Movie DNA vector.

Mirrors packages/shared/traits.json. The order of TRAIT_KEYS is the vector order and
must never change: stored vectors depend on it. To add a dimension, append it in the
JSON file first, append it here, then re-run the trait pipeline.
"""

import json
from functools import lru_cache
from pathlib import Path

_SHARED = Path(__file__).resolve().parents[3] / "packages" / "shared" / "traits.json"


@lru_cache
def _spec() -> dict:
    return json.loads(_SHARED.read_text(encoding="utf-8"))


@lru_cache
def trait_keys() -> tuple[str, ...]:
    return tuple(d["key"] for d in _spec()["dimensions"])


TRAIT_KEYS: tuple[str, ...] = trait_keys()
TRAIT_COUNT: int = len(TRAIT_KEYS)


def to_vector(traits: dict[str, float]) -> list[float]:
    """Dict of trait scores -> ordered vector. Missing dimensions default to 50 (neutral)."""
    return [float(traits.get(key, 50.0)) for key in TRAIT_KEYS]


def to_dict(vector: list[float]) -> dict[str, float]:
    """Ordered vector -> dict of trait scores."""
    if len(vector) != TRAIT_COUNT:
        raise ValueError(f"expected {TRAIT_COUNT} dimensions, got {len(vector)}")
    return dict(zip(TRAIT_KEYS, vector, strict=True))
