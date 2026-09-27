"""Match percentage and the reasons behind it. Pure functions: no DB, no network.

The formula is docs/TZ.md FR-5 (the user chose it over the cosine form that
docs/architecture.md used to give, 2026-09-27):

    d     = sqrt( Σ w[i]·(taste[i] - movie[i])² / Σ w[i] ) / 100
    match = round( 100 · (1 - d) )

for weights w (0..1), taste vector and movie vector, all in TRAIT_KEYS order on the
0..100 scale. 100·d is the weighted root-mean-square gap in trait points, so a film that
is on average 20 points away from the user's taste on the dimensions the user cares about
is an 80% match. The result is rounded half up.

Every input is a stored number (users.taste_vector, users.taste_weights,
movie_traits.vector), so any match the API returns can be recomputed by hand (CLAUDE.md).
"""

import math
from collections.abc import Mapping, Sequence

from app.traits import TRAIT_KEYS

# A dimension is only a reason when the user's taste and the film both reach this level:
# sharing a low score ("neither of you cares for romance") is not why someone likes a film.
REASON_FLOOR = 50.0


def weights_vector(weights: Mapping[str, float]) -> list[float]:
    """Stored weights ({trait_key: weight}, users.taste_weights) -> TRAIT_KEYS order."""
    missing = [key for key in TRAIT_KEYS if key not in weights]
    if missing:
        raise ValueError(f"weights missing for: {', '.join(missing)}")
    return [float(weights[key]) for key in TRAIT_KEYS]


def _check(taste: Sequence[float], weights: Sequence[float], movie: Sequence[float]) -> None:
    if not len(taste) == len(weights) == len(movie):
        raise ValueError(
            f"length mismatch: taste {len(taste)}, weights {len(weights)}, movie {len(movie)}"
        )
    if any(w < 0 or not math.isfinite(w) for w in weights):
        raise ValueError("weights must be finite and non-negative")


def weighted_gap(taste: Sequence[float], weights: Sequence[float], movie: Sequence[float]) -> float:
    """sqrt(Σ w·(t - m)² / Σ w): the weighted RMS gap in trait points, 0..100."""
    _check(taste, weights, movie)
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("the match is undefined when every weight is zero")
    squares = sum(w * (t - m) ** 2 for w, t, m in zip(weights, taste, movie, strict=True))
    return math.sqrt(squares / total_weight)


def match_percentage(
    taste: Sequence[float], weights: Sequence[float], movie_vector: Sequence[float]
) -> int:
    """0..100, per docs/TZ.md FR-5. Rounded half up (96.5 -> 97)."""
    raw = 100.0 - weighted_gap(taste, weights, movie_vector)  # = 100·(1 - d)
    return min(100, max(0, math.floor(raw + 0.5)))


def top_reasons(
    taste: Sequence[float],
    movie_vector: Sequence[float],
    n: int = 3,
    weights: Sequence[float] | None = None,
) -> list[str]:
    """The trait keys that the user's taste and the film share most, strongest first.

    A dimension's strength is w·min(t, m): the level both reach on it, scaled by how much
    the user cares about it. A film far below the user's taste on a dimension shares
    little of it; a film far above it shares no more than the user wants. Dimensions
    where either side is below REASON_FLOOR are never returned, so the list can be shorter
    than `n`. Ties keep TRAIT_KEYS order.
    """
    if weights is None:
        weights = [1.0] * len(taste)
    _check(taste, weights, movie_vector)
    if len(taste) != len(TRAIT_KEYS):
        raise ValueError(f"expected {len(TRAIT_KEYS)} dimensions, got {len(taste)}")
    strengths = [
        (w * min(t, m), index)
        for index, (w, t, m) in enumerate(zip(weights, taste, movie_vector, strict=True))
        if min(t, m) >= REASON_FLOOR and w > 0
    ]
    ranked = sorted(strengths, key=lambda s: (-s[0], s[1]))
    return [TRAIT_KEYS[index] for _, index in ranked[: max(n, 0)]]
