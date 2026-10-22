"""The rule for naming the traits behind a match: catalogue statistics plus two cuts.

The statistics (mean and population standard deviation of each trait over every film
with traits) come from one aggregate query and are kept in memory for a few minutes:
they move only when the trait pipeline scores more films. The cuts are settings
(`trait_reason_max_size`, `trait_reason_lean_min`, `trait_difference_min`). See
matching.trait_notes for the rule.
"""

import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.matching import DeviationRule, TraitStats
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


async def load_rule(session: AsyncSession) -> DeviationRule | None:
    """The deviation rule with the configured cuts; None while no film has traits."""
    stats = await trait_stats(session)
    if stats is None:
        return None
    settings = get_settings()
    return DeviationRule(
        stats=stats,
        reason_max_size=settings.trait_reason_max_size,
        reason_lean_min=settings.trait_reason_lean_min,
        difference_min=settings.trait_difference_min,
    )
