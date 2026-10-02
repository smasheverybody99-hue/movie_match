"""Catalogue statistics for the reason rule, read from movie_traits (test database)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services import reasons
from app.traits import TRAIT_COUNT, TRAIT_KEYS
from tests.integration.api import seed_films

A, B, C = 9_800_001, 9_800_002, 9_800_003


async def test_mean_and_population_sd_per_trait_in_trait_order(db_session: AsyncSession) -> None:
    # plot_twist (index 1): 20, 40, 90 -> mean 50, sd sqrt((900 + 100 + 1600) / 3)
    def v(twist: float) -> list[float]:
        return [twist if key == "plot_twist" else 60.0 for key in TRAIT_KEYS]

    await seed_films(db_session, {A: v(20), B: v(40), C: v(90), 9_800_004: None})
    stats = await reasons.trait_stats(db_session)
    assert stats is not None
    assert len(stats.mean) == len(stats.sd) == TRAIT_COUNT
    assert stats.mean[1] == pytest.approx(50.0)
    assert stats.sd[1] == pytest.approx((2600 / 3) ** 0.5)
    assert stats.mean[0] == pytest.approx(60.0) and stats.sd[0] == pytest.approx(0.0)


async def test_the_rule_carries_the_configured_thresholds(db_session: AsyncSession) -> None:
    await seed_films(db_session, {A: [50.0] * TRAIT_COUNT, B: [70.0] * TRAIT_COUNT})
    rule = await reasons.load_rule(db_session)
    settings = get_settings()
    assert rule is not None
    assert (rule.min_film_z, rule.min_taste_z) == (
        settings.reason_min_film_z,
        settings.reason_min_taste_z,
    )


async def test_the_statistics_are_kept_until_cleared(db_session: AsyncSession) -> None:
    await seed_films(db_session, {A: [50.0] * TRAIT_COUNT})
    first = await reasons.trait_stats(db_session)
    await seed_films(db_session, {B: [90.0] * TRAIT_COUNT})
    assert await reasons.trait_stats(db_session) == first  # cached
    reasons.clear_cache()
    again = await reasons.trait_stats(db_session)
    assert again is not None and again != first
