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

    One distance, `size`, decides both sides, but it means opposite things on them: a
    reason is a trait the film is CLOSE to the viewer on (`size <= reason_max_size`), a
    difference is one it is far from them on (`size >= difference_min`). The band between
    the two says nothing either way.

    `reason_lean_min` guards the reason side: closeness is only worth saying on a trait
    the viewer leans on, their taste at least that far from a typical film. Without it the
    traits where the viewer sits on the catalogue mean - the ones that say nothing about
    them - would be the ones named (TZ 1.27, ADR 0008, user's decision 2026-10-22).
    """

    stats: TraitStats
    reason_max_size: float = 0.35
    reason_lean_min: float = 0.40
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

    One distance, two meanings (TZ 1.27, FR-5; user's decision 2026-10-22). Per trait:

        size = |movie[i] - taste[i]| / sd[i]     how far the film sits from the viewer
        lean = |taste[i] - mean[i]| / sd[i]      how far the viewer sits from a typical film

        size <= rule.reason_max_size AND lean >= rule.reason_lean_min -> a reason
        size >= rule.difference_min                                   -> a difference
        otherwise                                                     -> nothing

    A reason is now closeness, not direction: "it suits you" says the film sits at the
    viewer's own level on a trait they have a definite taste for. This replaced the
    2026-10-15 rule, under which a reason meant the film went *further* the way the
    viewer leaned - so a film 17 points away from them could be a reason, and the
    generated sentence said "much gentler than you usually prefer" under a heading
    reading "Why it suits you" (the live contradiction of 2026-10-22, ADR 0008).

    Reasons are ranked by the SMALLEST size: the closest trait leads, because closeness
    is the claim. Differences are ranked by w·size, the largest first, so a dimension the
    viewer is consistent about counts for more. Reasons win: a film with any reason is
    described by its reasons, and differences speak only for a film that has none. Both
    empty means the panel says nothing.

    Every note can be checked by hand from the stored vectors and the catalogue: subtract
    two numbers and divide by the trait's sd. The match percentage (FR-5) does not use
    this at all. The list can be shorter than `n`. Ties keep TRAIT_KEYS order; a viewer
    sitting on the catalogue mean has no lean, so no trait of theirs can be a reason, and
    such a film speaks only through its differences, or not at all.
    """
    if weights is None:
        weights = [1.0] * len(taste)
    _check(taste, weights, movie_vector)
    if len(taste) != len(TRAIT_KEYS) or len(rule.stats.mean) != len(TRAIT_KEYS):
        raise ValueError(f"expected {len(TRAIT_KEYS)} dimensions, got {len(taste)}")
    if n <= 0:
        return TraitNotes()
    # Each side carries its own sort key, already signed so that the smallest comes first:
    # the closest trait leads a reason, the largest w·size leads a difference.
    found: dict[TraitSide, list[tuple[float, int]]] = {"reason": [], "difference": []}
    for index, (w, t, m) in enumerate(zip(weights, taste, movie_vector, strict=True)):
        mean, sd = rule.stats.mean[index], rule.stats.sd[index]
        if sd < 1e-9 or w <= 0:  # nothing can stand out on a trait the catalogue shares
            continue
        size = abs(m - t) / sd
        lean = abs(t - mean) / sd
        if size <= rule.reason_max_size and lean >= rule.reason_lean_min:
            found["reason"].append((size, index))
        if size >= rule.difference_min:
            found["difference"].append((-w * size, index))
    for side in ("reason", "difference"):
        if found[side]:
            ranked = sorted(found[side], key=lambda s: (s[0], s[1]))
            return TraitNotes(side, tuple(TRAIT_KEYS[i] for _, i in ranked[:n]))
    return TraitNotes()
