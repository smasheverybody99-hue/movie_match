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
from typing import Literal

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


def match_raw(
    taste: Sequence[float], weights: Sequence[float], movie_vector: Sequence[float]
) -> float:
    """100·(1 - d) before rounding: what the bands rank by, so ties on the integer do not
    decide which side of a cut a film falls."""
    return 100.0 - weighted_gap(taste, weights, movie_vector)


def match_percentage(
    taste: Sequence[float], weights: Sequence[float], movie_vector: Sequence[float]
) -> int:
    """0..100, per docs/TZ.md FR-5. Rounded half up (96.5 -> 97)."""
    raw = match_raw(taste, weights, movie_vector)
    return min(100, max(0, math.floor(raw + 0.5)))


# --- bands (TZ 1.13) --------------------------------------------------------------------
# The number is internal: it ranks and sorts, but did not predict the user's ratings
# (2026-10-05, AUC 0.52 on one account, docs/STATUS.md). The client shows a band instead,
# a claim about place rather than a score: the film is one of the user's N closest in the
# catalogue ("strong"), or in their closest share of it ("good").

MatchBand = Literal["strong", "good"]


@dataclass(frozen=True)
class BandCuts:
    """Raw match values (match_raw) at the cut places, for one user and one catalogue."""

    strong: float  # at place strong_top_n
    good: float  # at place ceil(good_share · N)
    floor: float  # at place ceil((1 - floor_share) · N): below it, never recommended


def _at_place(desc: Sequence[float], place: int) -> float:
    return desc[min(max(place, 1), len(desc)) - 1]


def band_cuts(
    raws: Sequence[float], strong_top_n: int, good_share: float, floor_share: float
) -> BandCuts | None:
    """The cuts from every catalogue film's raw match for this user; None for no films.

    Places count from 1 at the best film. A film whose raw value equals a cut is inside it.
    """
    if not raws:
        return None
    desc = sorted(raws, reverse=True)
    n = len(desc)
    return BandCuts(
        strong=_at_place(desc, strong_top_n),
        good=_at_place(desc, math.ceil(good_share * n)),
        floor=_at_place(desc, math.ceil((1.0 - floor_share) * n)),
    )


def match_band(raw: float, cuts: BandCuts | None) -> MatchBand | None:
    if cuts is None:
        return None
    if raw >= cuts.strong:
        return "strong"
    if raw >= cuts.good:
        return "good"
    return None


@dataclass(frozen=True)
class TraitStats:
    """The catalogue's mean and population standard deviation per trait, TRAIT_KEYS order."""

    mean: tuple[float, ...]
    sd: tuple[float, ...]


TraitSide = Literal["reason", "difference"]


@dataclass(frozen=True)
class DeviationRule:
    """When a trait is worth naming, and on which side. Cuts are in catalogue sds.

    Two cuts, not two rules: the same deviation and the same direction test decide both
    sides, and only the bar differs. A reason is cheap (0.5) because the panel's job is to
    say why a film suits someone; a difference is dear (1.0) because "this is not for you"
    is a hard claim and should be rare and unmistakable (TZ 1.23, user's decision).
    """

    stats: TraitStats
    reason_min: float = 0.5
    difference_min: float = 1.0


@dataclass(frozen=True)
class TraitNotes:
    """The traits worth naming for one (viewer, film), strongest first, and their side.

    One side only: a film that has reasons is described by its reasons. `side` is None
    exactly when `keys` is empty, and then the panel says nothing at all.
    """

    side: TraitSide | None = None
    keys: tuple[str, ...] = ()


def z_score(value: float, mean: float, sd: float) -> float | None:
    """How far `value` sits from the catalogue mean in standard deviations; None when the
    catalogue does not vary on the trait (nothing can stand out on it)."""
    return None if sd < 1e-9 else (value - mean) / sd


def trait_notes(
    taste: Sequence[float],
    movie_vector: Sequence[float],
    rule: DeviationRule,
    n: int = 3,
    weights: Sequence[float] | None = None,
) -> TraitNotes:
    """The traits worth naming for this film, and whether they are reasons or differences.

    One symmetric rule (TZ 1.23, FR-5; user's decision 2026-10-15). Per trait:

        deviation = movie[i] - taste[i]          how far the film sits from the viewer
        size      = |deviation| / sd[i]          in catalogue standard deviations
        lean      = taste[i] - mean[i]           which side of a typical film they sit on
        the same way as their lean, size >= rule.reason_min     -> a reason
        the other way,              size >= rule.difference_min -> a difference
        otherwise                                               -> nothing

    Strength is w·size, so a dimension the viewer is consistent about counts for more.
    Reasons win: a film with any reason is described by its reasons, and differences
    speak only for a film that has none. Both empty means the panel says nothing, which
    is the point - a film 3 points from the taste on a 20-point spread has nothing to say
    either way, and before this it was named as a reason anyway.

    Every note can be checked by hand from the stored vectors and the catalogue: subtract
    two numbers and divide by the trait's sd. The match percentage (FR-5) does not use
    this at all. The list can be shorter than `n`. Ties keep TRAIT_KEYS order; a viewer
    sitting exactly on the catalogue mean has no lean, and a deviation there is read as
    the other way, which needs the higher cut.
    """
    if weights is None:
        weights = [1.0] * len(taste)
    _check(taste, weights, movie_vector)
    if len(taste) != len(TRAIT_KEYS) or len(rule.stats.mean) != len(TRAIT_KEYS):
        raise ValueError(f"expected {len(TRAIT_KEYS)} dimensions, got {len(taste)}")
    if n <= 0:
        return TraitNotes()
    found: dict[TraitSide, list[tuple[float, int]]] = {"reason": [], "difference": []}
    for index, (w, t, m) in enumerate(zip(weights, taste, movie_vector, strict=True)):
        mean, sd = rule.stats.mean[index], rule.stats.sd[index]
        if sd < 1e-9 or w <= 0:  # nothing can stand out on a trait the catalogue shares
            continue
        deviation = m - t
        size = abs(deviation) / sd
        side: TraitSide = "reason" if (deviation > 0) == (t - mean > 0) else "difference"
        if size >= (rule.reason_min if side == "reason" else rule.difference_min):
            found[side].append((w * size, index))
    for side in ("reason", "difference"):
        if found[side]:
            ranked = sorted(found[side], key=lambda s: (-s[0], s[1]))
            return TraitNotes(side, tuple(TRAIT_KEYS[i] for _, i in ranked[:n]))
    return TraitNotes()
