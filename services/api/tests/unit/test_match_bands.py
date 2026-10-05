"""Match bands (FR-5, TZ 1.13): cut places over a hand-written catalogue. No DB."""

import pytest

from app.services.matching import (
    BandCuts,
    band_cuts,
    match_band,
    match_percentage,
    match_raw,
)
from app.traits import TRAIT_COUNT

# Twenty films whose raw match is 100, 99, ..., 81 (given out of order: the cuts sort).
RAWS = [100.0 - i for i in (7, 0, 19, 3, 12, 1, 18, 2, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 17)]


def test_cuts_are_the_values_at_the_places() -> None:
    cuts = band_cuts(RAWS, strong_top_n=5, good_share=0.35, floor_share=0.25)
    # place 5 -> 96; place ceil(0.35 * 20) = 7 -> 94; place ceil(0.75 * 20) = 15 -> 86
    assert cuts == BandCuts(strong=96.0, good=94.0, floor=86.0)


def test_a_value_on_a_cut_is_inside_it() -> None:
    cuts = BandCuts(strong=96.0, good=94.0, floor=86.0)
    assert match_band(96.0, cuts) == "strong"
    assert match_band(95.99, cuts) == "good"
    assert match_band(94.0, cuts) == "good"
    assert match_band(93.99, cuts) is None


def test_exactly_n_films_are_strong_without_ties() -> None:
    cuts = band_cuts(RAWS, strong_top_n=5, good_share=0.35, floor_share=0.25)
    bands = [match_band(raw, cuts) for raw in RAWS]
    assert bands.count("strong") == 5
    assert bands.count("good") == 2  # places 6 and 7
    assert sum(raw < cuts.floor for raw in RAWS) == 5  # places 16..20, the furthest 25%


def test_ties_on_the_cut_all_count() -> None:
    cuts = band_cuts([90.0, 90.0, 90.0, 80.0], strong_top_n=2, good_share=1.0, floor_share=0.0)
    assert [match_band(r, cuts) for r in (90.0, 90.0, 90.0)] == ["strong"] * 3


def test_a_small_catalogue_caps_the_places() -> None:
    cuts = band_cuts([70.0, 60.0], strong_top_n=5, good_share=0.35, floor_share=0.25)
    assert cuts == BandCuts(strong=60.0, good=70.0, floor=60.0)


def test_no_films_no_cuts_no_band() -> None:
    assert band_cuts([], strong_top_n=5, good_share=0.35, floor_share=0.25) is None
    assert match_band(99.0, None) is None


def test_the_band_ranks_the_same_numbers_the_match_rounds() -> None:
    taste, weights = [80.0] * TRAIT_COUNT, [1.0] * TRAIT_COUNT
    film = [70.0] * TRAIT_COUNT  # 10 points off everywhere
    assert match_raw(taste, weights, film) == pytest.approx(90.0)
    assert match_percentage(taste, weights, film) == 90
