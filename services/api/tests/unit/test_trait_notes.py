"""trait_notes: one distance, two meanings (TZ 1.27, ADR 0008, 2026-10-22).

A REASON is closeness - the film sits within `reason_max_size` of the viewer on a trait
their taste is at least `reason_lean_min` from a typical film on, so "it suits you" means
the two are at the same level on something the viewer actually has a taste for. A
DIFFERENCE is distance: `difference_min` away, whichever way. The band between the two
says nothing. Reasons win when both sides have something; reasons lead with the closest
trait, differences with the largest w-size. Hand-written catalogue statistics, no database.

This replaced the 2026-10-15 rule, under which a reason meant the film went *further* the
way the viewer leaned: a film 17 points away could be a reason, and the live sentence read
"much gentler than you usually prefer" under "Why it suits you"
(`test_the_live_contradiction_of_2026_10_22_is_gone`).
"""

from typing import get_args

import pytest

from app import schemas
from app.services.matching import DeviationRule, TraitNotes, TraitStats, trait_notes, z_score
from app.traits import TRAIT_COUNT, TRAIT_KEYS

# A catalogue where every trait averages 50 with sd 20, except visual_style: nearly every
# film scores high on it (mean 76, sd 14), as in the real 500-film catalogue. On sd 20 the
# reason window is 7 points (0.35), the lean guard 8 points (0.40) and a difference 20.
MEAN = {key: 50.0 for key in TRAIT_KEYS} | {"visual_style": 76.0}
SD = {key: 20.0 for key in TRAIT_KEYS} | {"visual_style": 14.0}
RULE = DeviationRule(
    TraitStats(tuple(MEAN[k] for k in TRAIT_KEYS), tuple(SD[k] for k in TRAIT_KEYS)),
    reason_max_size=0.35,
    reason_lean_min=0.40,
    difference_min=1.0,
)


def _vector(**values: float) -> list[float]:
    """Every trait at the catalogue mean unless named: no lean and no deviation elsewhere."""
    unknown = set(values) - set(TRAIT_KEYS)
    assert not unknown, unknown
    return [values.get(key, MEAN[key]) for key in TRAIT_KEYS]


def test_a_trait_the_film_matches_the_viewer_on_is_a_reason() -> None:
    taste = _vector(plot_twist=70, mystery=30)  # 1.0 sd above and below a typical film
    movie = _vector(plot_twist=74, mystery=27)  # 0.20 sd and 0.15 sd from the viewer
    assert trait_notes(taste, movie, RULE) == TraitNotes("reason", ("mystery", "plot_twist"))


def test_a_trait_the_viewer_has_no_lean_on_is_not_a_reason() -> None:
    """The guard TZ 1.27 added: matching someone on nothing in particular says nothing.

    Sitting on the catalogue mean is the live case - the account on the site sat 0.5
    points from the mean on violence, where every quiet film "suited" it.
    """
    taste = _vector(mystery=54)  # 0.20 sd from a typical film: no definite taste
    movie = _vector(mystery=56)  # 0.10 sd away, so as close as a film gets
    assert trait_notes(taste, movie, RULE) == TraitNotes(None, ())
    # Exactly on the mean has no lean at all, however close the film sits.
    assert trait_notes(_vector(mystery=50), _vector(mystery=50), RULE) == TraitNotes(None, ())
    # One point over the guard (8 points on sd 20) and the same closeness does speak.
    assert trait_notes(_vector(mystery=59), _vector(mystery=61), RULE) == TraitNotes(
        "reason", ("mystery",)
    )


def test_a_trait_the_film_sits_far_from_the_viewer_on_is_a_difference() -> None:
    taste = _vector(action=30)
    movie = _vector(action=95)  # 3.25 sd away
    assert trait_notes(taste, movie, RULE) == TraitNotes("difference", ("action",))
    # ...and the same in the other direction: a trait they want that the film lacks.
    assert trait_notes(_vector(romance=95), _vector(romance=20), RULE) == TraitNotes(
        "difference", ("romance",)
    )
    # A difference needs no lean: distance alone is the claim, so a viewer sitting on the
    # catalogue mean can still be told how a film differs from them.
    assert trait_notes(_vector(mystery=50), _vector(mystery=90), RULE) == TraitNotes(
        "difference", ("mystery",)
    )


def test_reasons_win_and_the_differences_stay_silent() -> None:
    taste = _vector(action=30, mystery=70)
    movie = _vector(action=95, mystery=72)  # action 3.25 sd away, mystery 0.10 sd away
    # The difference is by far the larger deviation and still does not speak.
    assert trait_notes(taste, movie, RULE) == TraitNotes("reason", ("mystery",))


def test_the_middle_band_says_nothing_either_way() -> None:
    """Between the two cuts there is no claim to make - the heart of TZ 1.27.

    Under the 2026-10-15 rule a 0.5 sd gap the way the viewer leaned was a reason, so a
    film 10 points away was called a match.
    """
    for film_value in (80.0, 60.0):  # 0.50 sd either side of a viewer who leans high
        assert trait_notes(_vector(mystery=70), _vector(mystery=film_value), RULE) == TraitNotes(
            None, ()
        ), film_value
    # Stage 5's case keeps its silence too: 3 points on sd 14 is close, but the viewer's
    # 85 is only 0.64 sd over a catalogue that averages 76 on visual_style... which clears
    # the lean guard, so here it is a reason - closeness is now the point.
    assert trait_notes(_vector(visual_style=85), _vector(visual_style=82), RULE) == TraitNotes(
        "reason", ("visual_style",)
    )


def test_reasons_are_ranked_by_the_smallest_size() -> None:
    taste = _vector(plot_twist=70, mystery=70, romance=70)  # the same lean on all three
    movie = _vector(plot_twist=76, mystery=72, romance=74)  # 0.30, 0.10, 0.20 sd away
    assert trait_notes(taste, movie, RULE, n=3).keys == ("mystery", "romance", "plot_twist")


def test_the_closest_trait_leads_even_with_the_smaller_lean() -> None:
    """Ranking is closeness, not the strength of the lean (user's decision, 2026-10-22)."""
    taste = _vector(mystery=59, plot_twist=90)  # lean 0.45 sd and 2.00 sd
    movie = _vector(mystery=60, plot_twist=96)  # 0.05 sd and 0.30 sd away
    assert trait_notes(taste, movie, RULE, n=2).keys == ("mystery", "plot_twist")


def test_differences_are_ranked_by_the_largest_weighted_size() -> None:
    taste = _vector(mystery=50, romance=50)
    movie = _vector(mystery=75, romance=90)  # 1.25 sd and 2.00 sd away
    assert trait_notes(taste, movie, RULE, n=2).keys == ("romance", "mystery")
    # A dimension the viewer is not consistent about counts for less: 2.00 x 0.5 < 1.25.
    weights = [0.5 if key == "romance" else 1.0 for key in TRAIT_KEYS]
    assert trait_notes(taste, movie, RULE, n=2, weights=weights).keys == ("mystery", "romance")


def test_a_side_is_set_exactly_when_a_trait_is_named() -> None:
    silent = trait_notes(_vector(), _vector(), RULE)
    assert silent.side is None and silent.keys == ()
    spoken = trait_notes(_vector(mystery=70), _vector(mystery=72), RULE)
    assert spoken.side is not None and spoken.keys


def test_a_trait_the_viewer_does_not_care_about_at_all_is_not_named() -> None:
    taste = _vector(mystery=70)
    movie = _vector(mystery=72)
    weights = [0.0 if key == "mystery" else 1.0 for key in TRAIT_KEYS]
    assert trait_notes(taste, movie, RULE, weights=weights) == TraitNotes(None, ())


def test_n_limits_the_list_and_ties_keep_trait_order() -> None:
    # Every trait but visual_style, which the catalogue spreads differently (sd 14), so
    # the rest sit the same 4 / 20 = 0.20 sd from the viewer and tie exactly.
    tied = [key for key in TRAIT_KEYS if key != "visual_style"]
    lean = _vector(**{key: MEAN[key] + 10 for key in tied})
    close = _vector(**{key: MEAN[key] + 14 for key in tied})
    notes = trait_notes(lean, close, RULE, n=3)
    assert notes.side == "reason"
    assert notes.keys == tuple(tied[:3])
    assert trait_notes(lean, close, RULE, n=TRAIT_COUNT).keys == tuple(tied)
    # Nothing to show means no side either, however well the film matches.
    assert trait_notes(lean, close, RULE, n=0) == TraitNotes(None, ())


def test_the_cuts_come_from_the_rule() -> None:
    taste, movie = _vector(mystery=70), _vector(mystery=78)  # lean 1.0 sd, 0.40 sd away
    assert trait_notes(taste, movie, RULE) == TraitNotes(None, ())  # outside the 0.35 window
    wider = DeviationRule(RULE.stats, reason_max_size=0.5, reason_lean_min=0.40)
    assert trait_notes(taste, movie, wider).keys == ("mystery",)
    # The lean guard is a cut of its own: the same film against a viewer with less of a
    # lean speaks only once the guard is lowered to meet it.
    mild = _vector(mystery=56)  # lean 0.30 sd
    assert trait_notes(mild, _vector(mystery=58), RULE) == TraitNotes(None, ())
    looser = DeviationRule(RULE.stats, reason_lean_min=0.25)
    assert trait_notes(mild, _vector(mystery=58), looser) == TraitNotes("reason", ("mystery",))
    # And the difference cut: 0.9 sd away is not enough for the harder one.
    assert trait_notes(_vector(mystery=50), _vector(mystery=68), RULE) == TraitNotes(None, ())
    nearer = DeviationRule(RULE.stats, difference_min=0.9)
    assert trait_notes(_vector(mystery=50), _vector(mystery=68), nearer) == TraitNotes(
        "difference", ("mystery",)
    )


def test_the_live_contradiction_of_2026_10_22_is_gone() -> None:
    """Up (14160) against the live account, with the real 500-film statistics.

    The old rule called this film a reason on ending_ambiguity and violence - the viewer
    sat 3.2 and 2.3 points below a typical film, the film 16 points below the viewer, the
    same way, over the 0.5 sd bar - and the sentence came back "much gentler than you
    usually prefer" under "Why it suits you". Under TZ 1.27 neither trait is close enough
    to be a reason, so the film is described by what it is: a comedy far funnier and far
    less mysterious than this viewer goes for.
    """
    real = {
        "ending_ambiguity": (28.8, 23.3, 25.6, 10.0),
        "violence": (44.0, 27.2, 41.7, 25.0),
        "humor": (32.6, 25.0, 32.0, 60.0),
        "mystery": (36.2, 22.8, 39.7, 15.0),
    }
    mean = tuple(real[k][0] if k in real else 50.0 for k in TRAIT_KEYS)
    sd = tuple(real[k][1] if k in real else 20.0 for k in TRAIT_KEYS)
    taste = [real[k][2] if k in real else 50.0 for k in TRAIT_KEYS]
    film = [real[k][3] if k in real else 50.0 for k in TRAIT_KEYS]
    rule = DeviationRule(TraitStats(mean, sd))
    assert trait_notes(taste, film, rule) == TraitNotes("difference", ("humor", "mystery"))


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
