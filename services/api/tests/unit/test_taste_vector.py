"""The taste vector from known ratings, by hand."""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.taste import (
    HALF_LIFE_DAYS,
    RatedFilm,
    build_profile,
    rating_weight,
    taste_vector,
)
from app.traits import TRAIT_COUNT

NOW = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)


def _film(score: float, value: float, days_ago: float = 0.0) -> RatedFilm:
    return RatedFilm(
        score=score, rated_at=NOW - timedelta(days=days_ago), vector=[value] * TRAIT_COUNT
    )


def test_known_ratings_give_the_expected_vector() -> None:
    films = [_film(9.0, 80.0), _film(7.0, 20.0), _film(3.0, 0.0)]
    # weights: 9 - 5 = 4, 7 - 5 = 2, and the 3 counts 0 (not liked)
    # taste = (4·80 + 2·20) / (4 + 2) = (320 + 40) / 6 = 60
    assert taste_vector(films, NOW) == pytest.approx([60.0] * TRAIT_COUNT)


def test_recent_ratings_weigh_more() -> None:
    old = _film(9.0, 0.0, days_ago=HALF_LIFE_DAYS)  # weight 4 · 0.5 = 2
    new = _film(9.0, 90.0)  # weight 4
    # taste = (2·0 + 4·90) / 6 = 60, closer to the recent film than the plain mean of 45
    assert taste_vector([old, new], NOW) == pytest.approx([60.0] * TRAIT_COUNT)


def test_rating_weight_halves_every_half_life() -> None:
    assert rating_weight(_film(10.0, 50.0), NOW) == pytest.approx(5.0)
    assert rating_weight(_film(10.0, 50.0, days_ago=HALF_LIFE_DAYS), NOW) == pytest.approx(2.5)
    assert rating_weight(_film(10.0, 50.0, days_ago=2 * HALF_LIFE_DAYS), NOW) == pytest.approx(1.25)


def test_a_future_timestamp_counts_as_now() -> None:
    assert rating_weight(_film(8.0, 50.0, days_ago=-3), NOW) == pytest.approx(3.0)


def test_disliked_films_do_not_pull_the_taste() -> None:
    liked = _film(8.0, 70.0)
    assert taste_vector([liked, _film(1.0, 0.0), _film(5.0, 0.0)], NOW) == pytest.approx(
        [70.0] * TRAIT_COUNT
    )


def test_no_liked_film_means_no_taste_vector() -> None:
    assert taste_vector([_film(5.0, 50.0), _film(2.0, 90.0)], NOW) is None
    assert taste_vector([], NOW) is None


def test_a_single_rating_does_not_produce_extreme_weights() -> None:
    profile = build_profile([_film(10.0, 95.0)], NOW)
    assert profile.vector == pytest.approx([95.0] * TRAIT_COUNT)
    # one favourite, spread 0, consistency 1: weight = (1·1 + 3·0.5) / (1 + 3) = 0.625
    assert profile.weights == pytest.approx([0.625] * TRAIT_COUNT)


def test_wrong_size_vector_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_profile([RatedFilm(score=9.0, rated_at=NOW, vector=[50.0] * 3)], NOW)
