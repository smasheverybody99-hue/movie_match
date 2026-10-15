"""trait_notes: one deviation measure, one direction test, two cuts (TZ 1.23, 2026-10-15).

A trait is named when the film sits far enough from the viewer's taste: the same way their
taste leans needs `reason_min` (0.5 sd), the other way needs `difference_min` (1.0 sd),
because "this film is not for you" is a hard claim and must be rare. Reasons win when both
sides have something. Hand-written catalogue statistics, no database.
"""

from typing import get_args

import pytest

from app import schemas
from app.services.matching import DeviationRule, TraitNotes, TraitStats, trait_notes, z_score
from app.traits import TRAIT_COUNT, TRAIT_KEYS

# A catalogue where every trait averages 50 with sd 20, except visual_style: nearly every
# film scores high on it (mean 76, sd 14), as in the real 500-film catalogue.
MEAN = {key: 50.0 for key in TRAIT_KEYS} | {"visual_style": 76.0}
SD = {key: 20.0 for key in TRAIT_KEYS} | {"visual_style": 14.0}
RULE = DeviationRule(
    TraitStats(tuple(MEAN[k] for k in TRAIT_KEYS), tuple(SD[k] for k in TRAIT_KEYS)),
    reason_min=0.5,
    difference_min=1.0,
)


def _vector(**values: float) -> list[float]:
    """Every trait at the catalogue mean unless named: no lean and no deviation elsewhere."""
    unknown = set(values) - set(TRAIT_KEYS)
    assert not unknown, unknown
    return [values.get(key, MEAN[key]) for key in TRAIT_KEYS]


def test_the_film_going_further_the_way_you_lean_is_a_reason() -> None:
    taste = _vector(plot_twist=70, mystery=70)  # leaning high on both
    movie = _vector(plot_twist=95, mystery=80)  # +25 = 1.25 sd, +10 = 0.50 sd
    assert trait_notes(taste, movie, RULE) == TraitNotes("reason", ("plot_twist", "mystery"))


def test_the_film_going_the_other_way_is_a_difference() -> None:
    taste = _vector(action=30)  # leaning low on action
    movie = _vector(action=95)  # +65 = 3.25 sd the other way
    assert trait_notes(taste, movie, RULE) == TraitNotes("difference", ("action",))
    # ...and the same in the other direction: a trait they want that the film lacks.
    taste = _vector(romance=95)
    movie = _vector(romance=20)  # -75 = 3.75 sd
    assert trait_notes(taste, movie, RULE) == TraitNotes("difference", ("romance",))


def test_reasons_win_when_a_film_has_both() -> None:
    taste = _vector(action=30, mystery=70)
    movie = _vector(action=95, mystery=85)  # action 3.25 sd away, mystery 0.75 sd further
    # The difference is by far the larger deviation and still does not speak.
    assert trait_notes(taste, movie, RULE) == TraitNotes("reason", ("mystery",))


def test_a_small_deviation_says_nothing_either_way() -> None:
    """Stage 5: 82 against 85 was named as a reason before this rule; now it is silence."""
    for taste_value, film_value in [(85.0, 82.0), (82.0, 85.0)]:
        notes = trait_notes(
            _vector(visual_style=taste_value), _vector(visual_style=film_value), RULE
        )
        assert notes == TraitNotes(None, ()), (taste_value, film_value)  # 3p on sd 14 = 0.21 sd
    # A deviation the other way that is real but not large keeps its silence too: it
    # clears the reason cut and is nowhere near the difference cut.
    assert trait_notes(_vector(mystery=70), _vector(mystery=56), RULE) == TraitNotes(None, ())


def test_a_side_is_set_exactly_when_a_trait_is_named() -> None:
    silent = trait_notes(_vector(), _vector(), RULE)
    assert silent.side is None and silent.keys == ()
    spoken = trait_notes(_vector(mystery=70), _vector(mystery=95), RULE)
    assert spoken.side is not None and spoken.keys


def test_a_viewer_with_no_lean_on_a_trait_only_gets_a_difference() -> None:
    # Their taste sits on the catalogue mean, so there is no direction to go "further" in.
    assert trait_notes(_vector(mystery=50), _vector(mystery=90), RULE) == TraitNotes(
        "difference", ("mystery",)
    )
    # 0.9 sd away is not enough for that harder cut.
    assert trait_notes(_vector(mystery=50), _vector(mystery=68), RULE) == TraitNotes(None, ())


def test_weights_reorder_the_named_traits() -> None:
    taste = _vector(mystery=70, romance=70)
    movie = _vector(mystery=80, romance=90)  # 0.5 sd and 1.0 sd, both the way they lean
    assert trait_notes(taste, movie, RULE, n=2).keys == ("romance", "mystery")
    weights = [0.4 if key == "romance" else 1.0 for key in TRAIT_KEYS]  # 0.4 < 0.5
    assert trait_notes(taste, movie, RULE, n=2, weights=weights).keys == ("mystery", "romance")


def test_a_trait_the_viewer_does_not_care_about_at_all_is_not_named() -> None:
    taste = _vector(mystery=70)
    movie = _vector(mystery=95)
    weights = [0.0 if key == "mystery" else 1.0 for key in TRAIT_KEYS]
    assert trait_notes(taste, movie, RULE, weights=weights) == TraitNotes(None, ())


def test_n_limits_the_list_and_ties_keep_trait_order() -> None:
    # Every trait but visual_style, which the catalogue spreads differently (sd 14), so
    # the rest deviate by the same 25 / 20 = 1.25 sd and tie exactly.
    tied = [key for key in TRAIT_KEYS if key != "visual_style"]
    lean = _vector(**{key: MEAN[key] + 10 for key in tied})
    further = _vector(**{key: MEAN[key] + 35 for key in tied})
    notes = trait_notes(lean, further, RULE, n=3)
    assert notes.side == "reason"
    assert notes.keys == tuple(tied[:3])
    assert trait_notes(lean, further, RULE, n=TRAIT_COUNT).keys == tuple(tied)
    # Nothing to show means no side either, however much the film deviates.
    assert trait_notes(lean, further, RULE, n=0) == TraitNotes(None, ())


def test_the_cuts_come_from_the_rule() -> None:
    taste, movie = _vector(mystery=70), _vector(mystery=84)  # 0.7 sd the way they lean
    assert trait_notes(taste, movie, RULE).keys == ("mystery",)
    strict = DeviationRule(RULE.stats, reason_min=1.0, difference_min=1.0)
    assert trait_notes(taste, movie, strict) == TraitNotes(None, ())
    # Symmetric cuts make the other side speak much more readily - what the 2026-10-15
    # measurement rejected, since it put difference text on 74% of film pages.
    away = _vector(mystery=56)  # 0.7 sd the other way
    assert trait_notes(taste, away, RULE) == TraitNotes(None, ())
    loose = DeviationRule(RULE.stats, reason_min=0.5, difference_min=0.5)
    assert trait_notes(taste, away, loose) == TraitNotes("difference", ("mystery",))


def test_a_trait_the_catalogue_does_not_vary_on_is_skipped() -> None:
    flat = DeviationRule(TraitStats(RULE.stats.mean, tuple(0.0 for _ in TRAIT_KEYS)))
    assert trait_notes(_vector(mystery=90), _vector(mystery=20), flat) == TraitNotes(None, ())
    assert z_score(70, 70, 0) is None
    assert z_score(90, 50, 20) == 2.0


def test_wrong_size_is_rejected() -> None:
    with pytest.raises(ValueError):
        trait_notes([50.0] * 3, [50.0] * 3, RULE)


def test_the_service_and_the_api_name_the_same_sides() -> None:
    assert get_args(schemas.TraitSide) == ("reason", "difference")
