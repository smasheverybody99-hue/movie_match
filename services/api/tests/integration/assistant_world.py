"""A small catalogue for the assistant's tests, and viewers with a taste.

The viewer loves films high on the first seven dimensions and low on the last seven. The
recorded answers (tests/fixtures/assistant/) refer to these ids:

    RATED      rated 9 by every viewer: never returned by a search
    SHORT      85 minutes, 2005, high on psychological complexity and plot twists
    LONG       150 minutes: outside runtime_max 90
    OLD_SHORT  80 minutes but 1970: outside year_min 1990

So the recorded tool call (runtime_max 90, year_min 1990, exclude 9600006) can only
return SHORT[:5].
"""

import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rating
from app.services.taste import recompute_taste
from app.services.users import ensure_user
from app.traits import TRAIT_COUNT
from tests.conftest import rolled_back_session
from tests.integration.api import seed_catalogue

HALF = TRAIT_COUNT // 2
UNKNOWN_ID = 424242  # in no database: the recorded answer names it anyway


def near(offset: float) -> list[float]:
    return [85.0 - offset] * HALF + [15.0 + offset] * HALF


def twisty(offset: float) -> list[float]:
    vector = near(offset)
    vector[0], vector[1] = 92.0, 90.0  # psychological_complexity, plot_twist
    return vector


RATED = [9_500_000 + i for i in range(1, 11)]
SHORT = [9_600_000 + i for i in range(1, 7)]
LONG = [9_610_000 + i for i in range(1, 7)]
OLD_SHORT = 9_620_001

CATALOGUE = [
    *(
        {"id": m, "vector": near(i % 3), "director": 100 + i, "release_date": "2000-01-01"}
        for i, m in enumerate(RATED)
    ),
    *(
        {
            "id": m,
            "vector": twisty(4 + i),
            "director": 200 + i,
            "runtime": 85,
            "release_date": "2005-06-01",
            "overview": f"A short puzzle film, number {i + 1}.",
            "genres": [(53, "Thriller")],
        }
        for i, m in enumerate(SHORT)
    ),
    *(
        {
            "id": m,
            "vector": near(2),
            "director": 300 + i,
            "runtime": 150,
            "release_date": "2010-01-01",
        }
        for i, m in enumerate(LONG)
    ),
    {
        "id": OLD_SHORT,
        "vector": twisty(3),
        "director": 400,
        "runtime": 80,
        "release_date": "1970-01-01",
    },
]


async def new_viewer(session: AsyncSession) -> uuid.UUID:
    """A fresh user who rated RATED 9: a taste profile and no assistant history."""
    user_id = uuid.uuid4()
    await ensure_user(session, user_id)
    for movie_id in RATED:
        session.add(Rating(user_id=user_id, movie_id=movie_id, score=9.0, liked_aspects=[]))
    await session.flush()
    await recompute_taste(session, user_id)
    await session.commit()
    return user_id


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def assistant_catalogue(migrated_test_db: None) -> AsyncIterator[AsyncSession]:
    """Seeded once per module and rolled back when it ends."""
    async with rolled_back_session() as session:
        await seed_catalogue(session, CATALOGUE)
        yield session
