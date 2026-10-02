"""The rule for naming the reasons behind a match: catalogue statistics plus thresholds.

The statistics (mean and population standard deviation of each trait over every film
with traits) come from one aggregate query and are kept in memory for a few minutes:
they move only when the trait pipeline scores more films. Thresholds are settings
(`reason_min_film_z`, `reason_min_taste_z`). See matching.top_reasons for the rule.
"""

import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.matching import ReasonRule, TraitStats
from app.traits import TRAIT_COUNT

CACHE_SECONDS = 600.0

_STATS_SQL = text(
    """
    SELECT u.i, avg(u.x), stddev_pop(u.x)
    FROM movie_traits t, unnest(t.vector::real[]) WITH ORDINALITY AS u(x, i)
    GROUP BY u.i
    ORDER BY u.i
    """
)

_cache: dict[str, tuple[float, TraitStats]] = {}


def clear_cache() -> None:
    """Forget the cached statistics (tests, or after a trait run in the same process)."""
    _cache.clear()


async def trait_stats(session: AsyncSession) -> TraitStats | None:
    """The catalogue's per-trait mean and sd; None while no film has traits."""
    hit = _cache.get("stats")
    if hit is not None and time.monotonic() - hit[0] < CACHE_SECONDS:
        return hit[1]
    rows = (await session.execute(_STATS_SQL)).all()
    if len(rows) != TRAIT_COUNT:
        return None
    stats = TraitStats(
        mean=tuple(float(mean) for _, mean, _ in rows),
        sd=tuple(float(sd or 0.0) for _, _, sd in rows),
    )
    _cache["stats"] = (time.monotonic(), stats)
    return stats


async def load_rule(session: AsyncSession) -> ReasonRule | None:
    """The reason rule with the configured thresholds; None while no film has traits."""
    stats = await trait_stats(session)
    if stats is None:
        return None
    settings = get_settings()
    return ReasonRule(
        stats=stats,
        min_film_z=settings.reason_min_film_z,
        min_taste_z=settings.reason_min_taste_z,
    )
