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
from dataclasses import dataclass

from app.traits import TRAIT_KEYS


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


@dataclass(frozen=True)
class TraitStats:
    """The catalogue's mean and population standard deviation per trait, TRAIT_KEYS order."""

    mean: tuple[float, ...]
    sd: tuple[float, ...]


@dataclass(frozen=True)
class ReasonRule:
    """What makes a trait a reason. Thresholds are in catalogue standard deviations."""

    stats: TraitStats
    min_film_z: float = 0.5
    min_taste_z: float = 0.0


def z_score(value: float, mean: float, sd: float) -> float | None:
    """How far `value` sits from the catalogue mean in standard deviations; None when the
    catalogue does not vary on the trait (nothing can stand out on it)."""
    return None if sd < 1e-9 else (value - mean) / sd


def top_reasons(
    taste: Sequence[float],
    movie_vector: Sequence[float],
    rule: ReasonRule,
    n: int = 3,
    weights: Sequence[float] | None = None,
) -> list[str]:
    """The traits on which this film stands out from typical films in the direction the
    user leans, strongest first. Only which traits are named changes here: the match
    percentage (FR-5) does not use this.

    A trait is a reason when the film is notably above the catalogue mean on it
    (z_film >= rule.min_film_z) and the user's taste is at least on the same side
    (z_taste >= rule.min_taste_z). Its strength is w·z_film. A trait nearly every film
    scores high on (2026-10-02: visual_style and emotional_intensity, mean ~74, sd 14)
    therefore no longer comes up for every film; with the old rule, w·min(taste, film),
    they were among the reasons for over 90% of one user's recommendations. Any reason can
    be checked by hand: z = (value - mean) / sd from the stored vectors and the catalogue.
    The list can be shorter than `n`, or empty. Ties keep TRAIT_KEYS order.
    """
    if weights is None:
        weights = [1.0] * len(taste)
    _check(taste, weights, movie_vector)
    if len(taste) != len(TRAIT_KEYS) or len(rule.stats.mean) != len(TRAIT_KEYS):
        raise ValueError(f"expected {len(TRAIT_KEYS)} dimensions, got {len(taste)}")
    strengths = []
    for index, (w, t, m) in enumerate(zip(weights, taste, movie_vector, strict=True)):
        mean, sd = rule.stats.mean[index], rule.stats.sd[index]
        z_film, z_taste = z_score(m, mean, sd), z_score(t, mean, sd)
        if z_film is None or z_taste is None or w <= 0:
            continue
        if z_film >= rule.min_film_z and z_taste >= rule.min_taste_z:
            strengths.append((w * z_film, index))
    ranked = sorted(strengths, key=lambda s: (-s[0], s[1]))
    return [TRAIT_KEYS[index] for _, index in ranked[: max(n, 0)]]
