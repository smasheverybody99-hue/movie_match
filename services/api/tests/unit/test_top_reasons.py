"""top_reasons names the traits on which a film stands out from typical films, in the
direction the user leans (2026-10-02). Hand-written catalogue statistics, no database."""

import pytest

from app.services.matching import ReasonRule, TraitStats, top_reasons, z_score
from app.traits import TRAIT_COUNT, TRAIT_KEYS

# A catalogue where every trait averages 50 with sd 20, except visual_style: nearly every
# film scores high on it (mean 76, sd 14), as in the real 500-film catalogue.
MEAN = {key: 50.0 for key in TRAIT_KEYS} | {"visual_style": 76.0}
SD = {key: 20.0 for key in TRAIT_KEYS} | {"visual_style": 14.0}
RULE = ReasonRule(
    TraitStats(tuple(MEAN[k] for k in TRAIT_KEYS), tuple(SD[k] for k in TRAIT_KEYS)),
    min_film_z=0.5,
    min_taste_z=0.0,
)


def _vector(**values: float) -> list[float]:
    """Every trait at the catalogue mean unless named: z = 0 everywhere else."""
    unknown = set(values) - set(TRAIT_KEYS)
    assert not unknown, unknown
    return [values.get(key, MEAN[key]) for key in TRAIT_KEYS]


def test_traits_where_the_film_stands_out_come_first_by_how_far() -> None:
    taste = _vector(plot_twist=70, mystery=70, darkness=70)
    movie = _vector(plot_twist=95, mystery=80, darkness=62)
    # z_film: twist 2.25, mystery 1.5, darkness 0.6 (all >= 0.5); taste above the mean
    assert top_reasons(taste, movie, RULE) == ["plot_twist", "mystery", "darkness"]


def test_a_trait_every_film_has_is_not_a_reason_for_every_film() -> None:
    # The bug of 2026-10-02: a film at 82 on visual_style is ordinary in this catalogue
    # (z = 0.43), so it is not named, however high the user's taste and weight are.
    taste = _vector(visual_style=85, humor=65)
    movie = _vector(visual_style=82, humor=65)
    weights = [1.0 if key == "visual_style" else 0.5 for key in TRAIT_KEYS]
    assert top_reasons(taste, movie, RULE, n=TRAIT_COUNT, weights=weights) == ["humor"]
    # A film that is striking even for this catalogue still is.
    assert "visual_style" in top_reasons(taste, _vector(visual_style=98), RULE)


def test_a_trait_the_user_leans_away_from_is_not_a_reason() -> None:
    taste = _vector(action=30, humor=60)  # below typical on action
    movie = _vector(action=95, humor=75)  # full of action
    assert top_reasons(taste, movie, RULE, n=TRAIT_COUNT) == ["humor"]


def test_a_trait_the_film_lacks_is_not_a_reason() -> None:
    taste = _vector(romance=95, mystery=60)
    movie = _vector(romance=20, mystery=65)
    assert top_reasons(taste, movie, RULE, n=TRAIT_COUNT) == ["mystery"]


def test_weights_reorder_the_reasons() -> None:
    taste = _vector(mystery=70, romance=70)
    movie = _vector(mystery=80, romance=90)  # z: mystery 1.5, romance 2.0
    assert top_reasons(taste, movie, RULE, n=2) == ["romance", "mystery"]
    weights = [0.5 if key == "romance" else 1.0 for key in TRAIT_KEYS]  # romance 1.0 < 1.5
    assert top_reasons(taste, movie, RULE, n=2, weights=weights) == ["mystery", "romance"]


def test_thresholds_come_from_the_rule() -> None:
    taste = _vector(mystery=52)  # z_taste 0.1
    movie = _vector(mystery=64)  # z_film 0.7
    assert top_reasons(taste, movie, RULE) == ["mystery"]
    strict = ReasonRule(RULE.stats, min_film_z=1.0, min_taste_z=0.0)
    assert top_reasons(taste, movie, strict) == []
    picky = ReasonRule(RULE.stats, min_film_z=0.5, min_taste_z=0.5)
    assert top_reasons(taste, movie, picky) == []


def test_n_limits_the_list_and_ties_keep_trait_order() -> None:
    high = _vector(**{key: MEAN[key] + 20 for key in TRAIT_KEYS if key != "visual_style"})
    reasons = top_reasons(high, high, RULE, n=3)
    assert reasons == [k for k in TRAIT_KEYS if k != "visual_style"][:3]
    assert top_reasons(high, high, RULE, n=0) == []


def test_an_ordinary_film_has_no_reasons() -> None:
    assert top_reasons(_vector(plot_twist=90), _vector(), RULE) == []


def test_a_trait_the_catalogue_does_not_vary_on_is_skipped() -> None:
    flat = ReasonRule(TraitStats(RULE.stats.mean, tuple(0.0 for _ in TRAIT_KEYS)))
    assert top_reasons(_vector(mystery=90), _vector(mystery=90), flat) == []
    assert z_score(70, 70, 0) is None
    assert z_score(90, 50, 20) == 2.0


def test_wrong_size_is_rejected() -> None:
    with pytest.raises(ValueError):
        top_reasons([50.0] * 3, [50.0] * 3, RULE)
