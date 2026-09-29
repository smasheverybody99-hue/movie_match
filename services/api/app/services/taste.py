"""The user's taste profile: a taste vector and per-dimension weights.

Both are built from the user's ratings and the rated films' trait vectors, recomputed on
every rating change (FR-4) and stored on `users`, where matching reads them.

Taste vector (TRAIT_KEYS order): the weighted mean of the trait vectors of the films the
user liked, where

    weight = (score - 5) * 0.5 ** (age_days / 180)

so a 9 counts twice as much as a 7, a rating half a year old counts half as much as one
from today, and films rated 5 or lower do not pull the taste towards themselves at all.
No liked film means no taste vector (None).

Weights: how consistent the user's favourites (rated 8 or higher) are on each dimension.

    consistency = 1 - spread / 50      spread: population standard deviation; 50 is the
                                        largest possible spread on a 0..100 scale
    weight      = (n * consistency + 3 * 0.5) / (n + 3)

The second line pulls every weight towards 0.5 until there are enough favourites to
trust, so one rating cannot produce extreme weights, and no weight is ever 0.
"""

import math
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MovieTraits, Rating, User
from app.traits import TRAIT_COUNT, TRAIT_KEYS

NEUTRAL_RATING = 5.0  # at or below this a rating adds nothing to the taste vector
HALF_LIFE_DAYS = 180.0
HIGH_RATING = 8.0  # the "favourites" that decide the weights (FR-3 uses 8.0 too)
MAX_SPREAD = 50.0
WEIGHT_PRIOR = 0.5
PRIOR_STRENGTH = 3.0  # favourites it takes before the data outweighs the prior


@dataclass(frozen=True)
class RatedFilm:
    score: float  # 0.5 .. 10.0
    rated_at: datetime
    vector: Sequence[float]  # the film's traits, TRAIT_KEYS order


@dataclass(frozen=True)
class TasteProfile:
    vector: list[float] | None  # None until the user has liked a film
    weights: list[float]


def rating_weight(film: RatedFilm, now: datetime) -> float:
    """How much one rating pulls the taste vector. 0 for a rating of 5 or lower."""
    preference = max(film.score - NEUTRAL_RATING, 0.0)
    age_days = max((now - film.rated_at).total_seconds() / 86_400, 0.0)
    return preference * 0.5 ** (age_days / HALF_LIFE_DAYS)


def taste_vector(films: Sequence[RatedFilm], now: datetime) -> list[float] | None:
    weighted = [(rating_weight(f, now), f.vector) for f in films]
    total = sum(w for w, _ in weighted)
    if total == 0:
        return None
    return [sum(w * vector[i] for w, vector in weighted) / total for i in range(TRAIT_COUNT)]


def taste_weights(films: Sequence[RatedFilm]) -> list[float]:
    favourites = [f.vector for f in films if f.score >= HIGH_RATING]
    n = len(favourites)
    weights = []
    for i in range(TRAIT_COUNT):
        values = [vector[i] for vector in favourites]
        if n:
            mean = sum(values) / n
            spread = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
            consistency = min(max(1.0 - spread / MAX_SPREAD, 0.0), 1.0)
        else:
            consistency = WEIGHT_PRIOR
        weights.append((n * consistency + PRIOR_STRENGTH * WEIGHT_PRIOR) / (n + PRIOR_STRENGTH))
    return weights


def build_profile(films: Sequence[RatedFilm], now: datetime) -> TasteProfile:
    for film in films:
        if len(film.vector) != TRAIT_COUNT:
            raise ValueError(f"expected {TRAIT_COUNT} dimensions, got {len(film.vector)}")
    return TasteProfile(vector=taste_vector(films, now), weights=taste_weights(films))


# --- database side ----------------------------------------------------------------


async def load_rated_films(session: AsyncSession, user_id: uuid.UUID) -> list[RatedFilm]:
    """The user's ratings of films that have a trait vector. Unscored films are skipped."""
    rows = await session.execute(
        select(Rating.score, Rating.updated_at, MovieTraits.vector)
        .join(MovieTraits, MovieTraits.movie_id == Rating.movie_id)
        .where(Rating.user_id == user_id)
        .order_by(Rating.movie_id)
    )
    return [
        RatedFilm(score=score, rated_at=rated_at, vector=[float(v) for v in vector])
        for score, rated_at, vector in rows.all()
    ]


async def recompute_taste(
    session: AsyncSession, user_id: uuid.UUID, now: datetime | None = None
) -> TasteProfile | None:
    """Rebuild and store the user's profile. Flushes; the caller commits.

    Without a liked film there is no taste to store, and both columns are cleared.
    """
    now = now or datetime.now(UTC)
    profile = build_profile(await load_rated_films(session, user_id), now)
    user = await session.get(User, user_id)
    if user is None:
        raise LookupError(f"no user {user_id}")
    if profile.vector is None:
        user.taste_vector = None
        user.taste_weights = None
    else:
        user.taste_vector = profile.vector
        user.taste_weights = dict(zip(TRAIT_KEYS, profile.weights, strict=True))
    user.taste_updated_at = now
    await session.flush()
    return profile if profile.vector is not None else None
