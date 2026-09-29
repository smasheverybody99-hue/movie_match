"""Per-dimension weights: consistent favourites weigh high, scattered ones low."""

import math
from datetime import UTC, datetime

import pytest

from app.services.taste import RatedFilm, taste_weights
from app.traits import TRAIT_COUNT

NOW = datetime(2026, 9, 27, tzinfo=UTC)


def _film(score: float, first: float, second: float) -> RatedFilm:
    return RatedFilm(score=score, rated_at=NOW, vector=[first, second] + [50.0] * (TRAIT_COUNT - 2))


def test_tight_cluster_weighs_high_and_scattered_weighs_low() -> None:
    favourites = [_film(9.0, 70, 0), _film(8.5, 70, 100), _film(10.0, 70, 50)]
    weights = taste_weights(favourites)
    # dimension 1: 70, 70, 70 -> spread 0, consistency 1
    #   weight = (3·1 + 3·0.5) / (3 + 3) = 4.5 / 6 = 0.75
    assert weights[0] == pytest.approx(0.75)
    # dimension 2: 0, 100, 50 -> mean 50, spread sqrt((2500 + 2500 + 0) / 3) = 40.82
    #   consistency = 1 - 40.82 / 50 = 0.1835
    #   weight = (3·0.1835 + 1.5) / 6 = 0.3417
    spread = math.sqrt(5000 / 3)
    assert weights[1] == pytest.approx((3 * (1 - spread / 50) + 1.5) / 6)
    assert weights[1] == pytest.approx(0.3417, abs=1e-4)
    assert weights[0] > weights[1]


def test_only_favourites_decide_the_weights() -> None:
    favourites = [_film(9.0, 70, 70), _film(9.0, 70, 70)]
    noise = [_film(6.0, 0, 100), _film(2.0, 100, 0)]  # below 8: ignored
    assert taste_weights(favourites + noise) == taste_weights(favourites)


def test_more_evidence_moves_further_from_the_prior() -> None:
    few = taste_weights([_film(9.0, 70, 70)])
    many = taste_weights([_film(9.0, 70, 70)] * 12)
    # a perfectly consistent dimension: 0.625 with one favourite, (12 + 1.5) / 15 = 0.9 with 12
    assert few[0] == pytest.approx(0.625)
    assert many[0] == pytest.approx(0.9)


def test_no_favourites_gives_the_neutral_prior() -> None:
    assert taste_weights([_film(7.0, 0, 100)]) == pytest.approx([0.5] * TRAIT_COUNT)
    assert taste_weights([]) == pytest.approx([0.5] * TRAIT_COUNT)


def test_weights_stay_in_range_and_never_reach_zero() -> None:
    # the most scattered case possible: favourites at 0 and 100 on every dimension
    scattered = [
        RatedFilm(score=9.0, rated_at=NOW, vector=[v] * TRAIT_COUNT) for v in (0.0, 100.0) * 20
    ]
    weights = taste_weights(scattered)
    assert all(0 < w <= 1 for w in weights)
    # spread 50, consistency 0: weight = (40·0 + 1.5) / 43
    assert weights[0] == pytest.approx(1.5 / 43)
