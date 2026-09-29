"""top_reasons names the dimensions the taste and the film share most, strongest first."""

import pytest

from app.services.matching import top_reasons
from app.traits import TRAIT_COUNT, TRAIT_KEYS


def _vector(**values: float) -> list[float]:
    """All dimensions at `default` unless named."""
    default = values.pop("default", 10.0)
    unknown = set(values) - set(TRAIT_KEYS)
    assert not unknown, unknown
    return [values.get(key, default) for key in TRAIT_KEYS]


def test_shared_high_dimensions_come_first_in_order() -> None:
    taste = _vector(psychological_complexity=90, plot_twist=80, darkness=70)
    movie = _vector(psychological_complexity=95, plot_twist=90, darkness=60)
    # strength w·min(t, m): complexity 90, twist 80, darkness 60; everything else 10,
    # below the floor of 50
    assert top_reasons(taste, movie) == ["psychological_complexity", "plot_twist", "darkness"]


def test_a_trait_only_the_film_has_is_not_a_reason() -> None:
    taste = _vector(humor=90, action=0)
    movie = _vector(humor=80, action=100)  # full of action, but the user scores it 0
    assert top_reasons(taste, movie, n=TRAIT_COUNT) == ["humor"]


def test_a_trait_the_film_lacks_is_not_a_reason() -> None:
    taste = _vector(romance=95, mystery=60)
    movie = _vector(romance=20, mystery=65)  # the user loves romance; this film has little
    assert top_reasons(taste, movie, n=TRAIT_COUNT) == ["mystery"]


def test_weights_reorder_the_reasons() -> None:
    taste = _vector(mystery=70, romance=90)
    movie = _vector(mystery=80, romance=90)
    # strengths: romance min(90, 90) = 90, mystery min(70, 80) = 70
    assert top_reasons(taste, movie, n=2) == ["romance", "mystery"]
    # romance at w = 0.5: 45 < 70
    weights = [0.5 if key == "romance" else 1.0 for key in TRAIT_KEYS]
    assert top_reasons(taste, movie, n=2, weights=weights) == ["mystery", "romance"]


def test_n_limits_the_list() -> None:
    taste = _vector(default=50)
    assert len(top_reasons(taste, taste, n=3)) == 3
    assert top_reasons(taste, taste, n=0) == []


def test_nothing_shared_means_no_reasons() -> None:
    assert top_reasons(_vector(default=40), _vector(default=90)) == []


def test_ties_keep_trait_order() -> None:
    same = _vector(default=50)
    assert top_reasons(same, same, n=2) == list(TRAIT_KEYS[:2])


def test_wrong_size_is_rejected() -> None:
    with pytest.raises(ValueError):
        top_reasons([50.0] * 3, [50.0] * 3)
