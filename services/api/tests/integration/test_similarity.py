"""find_similar with hand-made vectors, so the expected order is known exactly.

Every embedding lies in the plane of the first two dimensions, at a chosen angle from
the seed film. Cosine distance is then 1 - cos(angle): the smaller the angle, the nearer.
"""

import math
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EMBEDDING_DIM, Movie, MovieEmbedding, MovieTraits
from app.services.similarity import NoEmbedding, SimilarityFilters, find_similar
from app.traits import TRAIT_KEYS, to_vector

SEED = 9_000_001

# id: (angle from seed in degrees, year, runtime, language, violence)
FILMS = {
    SEED: (0, 1999, 139, "en", 80),
    9_000_002: (10, 2003, 120, "en", 20),
    9_000_003: (30, 1972, 175, "it", 90),
    9_000_004: (60, 2010, 95, "ja", 40),
    9_000_005: (90, 2015, 150, "ko", 10),
}
NO_EMBEDDING = 9_000_006


def _embedding(angle_degrees: float) -> list[float]:
    radians = math.radians(angle_degrees)
    return [math.cos(radians), math.sin(radians)] + [0.0] * (EMBEDDING_DIM - 2)


@pytest.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    for movie_id, (angle, year, runtime, language, violence) in FILMS.items():
        scores = {key: 50.0 for key in TRAIT_KEYS} | {"violence": float(violence)}
        db_session.add(
            Movie(
                id=movie_id,
                title=f"Film {movie_id}",
                release_date=date(year, 6, 1),
                runtime_minutes=runtime,
                original_language=language,
            )
        )
        await db_session.flush()
        db_session.add(
            MovieTraits(movie_id=movie_id, scores=scores, vector=to_vector(scores), model="fixture")
        )
        db_session.add(
            MovieEmbedding(movie_id=movie_id, embedding=_embedding(angle), model="fixture")
        )
    db_session.add(Movie(id=NO_EMBEDDING, title="Not embedded yet"))
    await db_session.flush()
    return db_session


def _ids(results) -> list[int]:
    return [r.movie_id for r in results]


async def test_neighbours_come_back_nearest_first(seeded: AsyncSession) -> None:
    results = await find_similar(seeded, SEED, limit=10)
    assert _ids(results) == [9_000_002, 9_000_003, 9_000_004, 9_000_005]
    expected = [1 - math.cos(math.radians(a)) for a in (10, 30, 60, 90)]
    assert [r.distance for r in results] == pytest.approx(expected, abs=1e-6)


async def test_seed_film_is_excluded(seeded: AsyncSession) -> None:
    assert SEED not in _ids(await find_similar(seeded, SEED))


async def test_limit(seeded: AsyncSession) -> None:
    assert _ids(await find_similar(seeded, SEED, limit=2)) == [9_000_002, 9_000_003]


async def test_trait_vectors_are_attached_in_trait_order(seeded: AsyncSession) -> None:
    first = (await find_similar(seeded, SEED, limit=1))[0]
    assert len(first.traits) == len(TRAIT_KEYS)
    assert first.traits[TRAIT_KEYS.index("violence")] == 20.0
    assert first.year == 2003


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        (SimilarityFilters(year_min=2000), [9_000_002, 9_000_004, 9_000_005]),
        (SimilarityFilters(year_max=2005), [9_000_002, 9_000_003]),
        (SimilarityFilters(year_min=2000, year_max=2012), [9_000_002, 9_000_004]),
        (SimilarityFilters(runtime_min=121), [9_000_003, 9_000_005]),
        (SimilarityFilters(runtime_max=120), [9_000_002, 9_000_004]),
        (SimilarityFilters(languages=("ja", "ko")), [9_000_004, 9_000_005]),
        (SimilarityFilters(max_violence=40), [9_000_002, 9_000_004, 9_000_005]),
        (SimilarityFilters(max_violence=10), [9_000_005]),
    ],
)
async def test_each_filter_is_respected(
    seeded: AsyncSession, filters: SimilarityFilters, expected: list[int]
) -> None:
    assert _ids(await find_similar(seeded, SEED, limit=10, filters=filters)) == expected


async def test_filters_that_exclude_everything_return_nothing(seeded: AsyncSession) -> None:
    assert await find_similar(seeded, SEED, filters=SimilarityFilters(languages=("zz",))) == []


async def test_seed_without_embedding_raises(seeded: AsyncSession) -> None:
    with pytest.raises(NoEmbedding):
        await find_similar(seeded, NO_EMBEDDING)


async def test_unknown_seed_raises(seeded: AsyncSession) -> None:
    with pytest.raises(NoEmbedding):
        await find_similar(seeded, 1)
