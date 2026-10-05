"""Match bands for a user: where a film's match places it in the catalogue (TZ 1.13, FR-5).

The cuts are three raw match values (matching.band_cuts) computed from every film with
traits. Ranking the catalogue for one user is cheap (measured 2026-10-05: 4 ms for 500
films, 68 ms for 5 000) but needs every film's vector, so two things are kept in memory:

- the catalogue's trait vectors, for a few minutes (they change only when the trait
  pipeline scores more films), like reasons.trait_stats;
- each user's cuts, keyed by users.taste_updated_at, so a rating (which recomputes the
  taste) gives new cuts, and by the catalogue load, so new films do too.

Every cut can be checked by hand: rank match_raw over the stored vectors and read the
value at the place (settings: match_strong_top_n, match_good_share, match_floor_share).
"""

import time
import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import MovieTraits
from app.services.matching import BandCuts, band_cuts, match_raw

CACHE_SECONDS = 600.0
MAX_USERS_CACHED = 10_000

_catalogue: dict[str, tuple[float, list[list[float]]]] = {}
_cuts: dict[tuple[uuid.UUID, datetime | None, float], BandCuts | None] = {}


def clear_cache() -> None:
    """Forget the catalogue and every user's cuts (tests, or after a trait run)."""
    _catalogue.clear()
    _cuts.clear()


async def _catalogue_vectors(session: AsyncSession) -> tuple[float, list[list[float]]]:
    hit = _catalogue.get("vectors")
    if hit is not None and time.monotonic() - hit[0] < CACHE_SECONDS:
        return hit
    rows = await session.scalars(select(MovieTraits.vector))
    loaded = (time.monotonic(), [[float(v) for v in vector] for vector in rows.all()])
    _catalogue["vectors"] = loaded
    _cuts.clear()  # every cached cut was computed from the old catalogue
    return loaded


async def load_cuts(
    session: AsyncSession,
    user_id: uuid.UUID,
    taste_updated_at: datetime | None,
    taste: Sequence[float],
    weights: Sequence[float],
) -> BandCuts | None:
    """The user's cuts; None while no film has traits."""
    loaded_at, vectors = await _catalogue_vectors(session)
    key = (user_id, taste_updated_at, loaded_at)
    if key in _cuts:
        return _cuts[key]
    settings = get_settings()
    cuts = band_cuts(
        [match_raw(taste, weights, vector) for vector in vectors],
        strong_top_n=settings.match_strong_top_n,
        good_share=settings.match_good_share,
        floor_share=settings.match_floor_share,
    )
    if len(_cuts) >= MAX_USERS_CACHED:
        _cuts.clear()
    _cuts[key] = cuts
    return cuts
