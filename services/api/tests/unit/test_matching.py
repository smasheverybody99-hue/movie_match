"""The match formula of docs/TZ.md FR-5, checked against hand arithmetic."""

import pytest

from app.services.matching import match_percentage, weighted_gap, weights_vector
from app.traits import TRAIT_COUNT, TRAIT_KEYS

UNIFORM = [1.0] * TRAIT_COUNT
REST = [50.0] * (TRAIT_COUNT - 3)  # the example differs on three dimensions; the rest agree


def test_identical_vectors_give_100() -> None:
    fight_club = [92, 95, 70, 88, 78, 66, 35, 22, 58, 80, 85, 55, 86, 48]
    assert match_percentage(fight_club, UNIFORM, fight_club) == 100


def test_maximally_different_vectors_give_0() -> None:
    # A gap of 100 on every dimension: d = sqrt(14·100² / 14) / 100 = 1.
    assert match_percentage([0.0] * TRAIT_COUNT, UNIFORM, [100.0] * TRAIT_COUNT) == 0


def test_matches_the_hand_computed_example() -> None:
    taste = [90.0, 10.0, 50.0, *REST]
    movie = [90.0, 90.0, 50.0, *REST]
    # Uniform weights, 14 dimensions; only the second differs, by 80:
    #   Σ w·(t - m)² = 80²          = 6400
    #   Σ w          = 14
    #   100·d = sqrt(6400 / 14) = sqrt(457.142857) = 21.38090
    #   match = 100 - 21.38090 = 78.619  ->  79
    assert weighted_gap(taste, UNIFORM, movie) == pytest.approx(21.38090, abs=1e-5)
    assert match_percentage(taste, UNIFORM, movie) == 79

    # The user is inconsistent on the second dimension, w = 0.1 there, 1 elsewhere:
    #   Σ w·(t - m)² = 0.1 · 6400    = 640
    #   Σ w          = 13 + 0.1      = 13.1
    #   100·d = sqrt(640 / 13.1) = sqrt(48.854962) = 6.98963
    #   match = 100 - 6.98963 = 93.010  ->  93
    weights = [1.0, 0.1, *([1.0] * (TRAIT_COUNT - 2))]
    assert weighted_gap(taste, weights, movie) == pytest.approx(6.98963, abs=1e-5)
    assert match_percentage(taste, weights, movie) == 93


def test_weights_change_the_result() -> None:
    taste = [90.0, 10.0, 50.0, *REST]
    movie = [90.0, 90.0, 50.0, *REST]
    indifferent = [1.0, 0.1, *([1.0] * (TRAIT_COUNT - 2))]
    assert match_percentage(taste, UNIFORM, movie) < match_percentage(taste, indifferent, movie)


def test_scaling_all_weights_changes_nothing() -> None:
    taste = [90.0, 10.0, 50.0, *REST]
    movie = [90.0, 90.0, 50.0, *REST]
    halved = [0.5] * TRAIT_COUNT
    assert weighted_gap(taste, halved, movie) == pytest.approx(weighted_gap(taste, UNIFORM, movie))


def test_size_matters_not_only_direction() -> None:
    """Pinned: the cosine form once in docs/architecture.md scored this pair 100.

    A taste of 30 everywhere and a film of 90 everywhere are 60 points apart on every
    dimension: match = 100 - 60 = 40.
    """
    assert match_percentage([30.0] * TRAIT_COUNT, UNIFORM, [90.0] * TRAIT_COUNT) == 40


def test_rounds_half_up() -> None:
    # Only the first dimension has weight; a gap of 3.5 there gives exactly 96.5.
    # Python's round() would give 96; the formula rounds half up to 97.
    weights = [1.0] + [0.0] * (TRAIT_COUNT - 1)
    taste = [50.0] * TRAIT_COUNT
    movie = [53.5] + [50.0] * (TRAIT_COUNT - 1)
    assert weighted_gap(taste, weights, movie) == 3.5
    assert match_percentage(taste, weights, movie) == 97


def test_all_zero_weights_are_rejected() -> None:
    with pytest.raises(ValueError, match="undefined"):
        match_percentage([50.0] * TRAIT_COUNT, [0.0] * TRAIT_COUNT, [50.0] * TRAIT_COUNT)


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        match_percentage([50.0] * TRAIT_COUNT, [-1.0, *UNIFORM[1:]], [50.0] * TRAIT_COUNT)


def test_length_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="length"):
        match_percentage([50.0] * TRAIT_COUNT, UNIFORM, [50.0] * (TRAIT_COUNT - 1))


def test_stored_weights_are_read_in_trait_order() -> None:
    stored = {key: float(i) for i, key in enumerate(reversed(TRAIT_KEYS))}
    assert weights_vector(stored) == [stored[key] for key in TRAIT_KEYS]


def test_stored_weights_with_a_missing_key_are_rejected() -> None:
    stored = {key: 1.0 for key in TRAIT_KEYS[1:]}
    with pytest.raises(ValueError, match=TRAIT_KEYS[0]):
        weights_vector(stored)
