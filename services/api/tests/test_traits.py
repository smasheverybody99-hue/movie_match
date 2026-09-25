import pytest

from app.pipelines.traits import parse_response
from app.traits import TRAIT_COUNT, TRAIT_KEYS, to_dict, to_vector


def test_vector_roundtrip() -> None:
    scores = {key: float(i * 3 % 101) for i, key in enumerate(TRAIT_KEYS)}
    assert to_dict(to_vector(scores)) == scores


def test_missing_traits_default_to_neutral() -> None:
    vector = to_vector({TRAIT_KEYS[0]: 90.0})
    assert len(vector) == TRAIT_COUNT
    assert vector[0] == 90.0
    assert all(value == 50.0 for value in vector[1:])


def test_parse_response_rejects_missing_key() -> None:
    payload = "{" + ", ".join(f'"{k}": 50' for k in TRAIT_KEYS[:-1]) + "}"
    with pytest.raises(ValueError, match="missing trait"):
        parse_response(payload)


def test_parse_response_rejects_out_of_range() -> None:
    body = {k: 50 for k in TRAIT_KEYS}
    body[TRAIT_KEYS[0]] = 140
    import json

    with pytest.raises(ValueError, match="out of range"):
        parse_response(json.dumps(body))
