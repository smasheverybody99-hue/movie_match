"""GET /recommendations against the test database, with a hand-built catalogue.

The user loves films high on the first seven dimensions and low on the last seven
(TASTE). Candidates are placed at known distances from that taste, so which films may
appear, and roughly how well they match, is decided by the fixture, not by chance.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Dismissal, MovieTraits, Rating, User, WatchlistItem
from app.services.matching import match_percentage, top_reasons, weights_vector
from app.services.reasons import load_rule
from app.services.recommend import MAX_PER_DIRECTOR, MIN_MATCH
from app.services.taste import recompute_taste
from app.services.users import ensure_user
from app.traits import TRAIT_COUNT
from tests.conftest import requires_db, rolled_back_session
from tests.integration.api import api_client, auth, seed_catalogue

HALF = TRAIT_COUNT // 2
TASTE = [85.0] * HALF + [15.0] * HALF


def near(offset: float) -> list[float]:
    """TASTE moved `offset` points on every dimension (towards 50)."""
    return [85.0 - offset] * HALF + [15.0 + offset] * HALF


RATED = [9_500_000 + i for i in range(1, 11)]
AUTEUR = 7_000_001  # directs four excellent candidates; the cap allows two per section
BY_AUTEUR = [9_510_001, 9_510_002, 9_510_003, 9_510_004]
GOOD = [9_520_000 + i for i in range(1, 9)]
# Enough strong long films to fill "For you" (20) and "Because you loved" (10), so the
# short ones, which match a little less, are left for "Under 90 minutes". A film is shown
# in one section only.
FILLERS = [9_560_000 + i for i in range(1, 31)]
SHORT = [9_530_000 + i for i in range(1, 7)]
BAD = [9_540_001, 9_540_002]  # opposite taste: ~30% match
BELOW_CUT = 9_540_003  # 45 points off everywhere: 55%, just under the 60% cut
DISMISSED = 9_550_001
WATCHED = 9_550_002

CATALOGUE = [
    *({"id": m, "vector": near(i % 3), "director": 1_000 + i} for i, m in enumerate(RATED)),
    *({"id": m, "vector": near(2), "director": AUTEUR} for m in BY_AUTEUR),
    *({"id": m, "vector": near(8 + i), "director": 2_000 + i} for i, m in enumerate(GOOD)),
    *({"id": m, "vector": near(3), "director": 8_000 + i} for i, m in enumerate(FILLERS)),
    *(
        {"id": m, "vector": near(20), "director": 3_000 + i, "runtime": 80 + i}
        for i, m in enumerate(SHORT)
    ),
    *({"id": m, "vector": [15.0] * HALF + [85.0] * HALF, "director": 4_000} for m in BAD),
    {"id": BELOW_CUT, "vector": near(45), "director": 5_000},
    {"id": DISMISSED, "vector": near(1), "director": 6_000},
    {"id": WATCHED, "vector": near(1), "director": 6_001},
]


async def _rate(session: AsyncSession, user_id: uuid.UUID, movie_ids: list[int]) -> None:
    """Ratings written directly, then one taste recompute: the ratings API has its own tests."""
    await ensure_user(session, user_id)
    for movie_id in movie_ids:
        session.add(Rating(user_id=user_id, movie_id=movie_id, score=9.0, liked_aspects=[]))
    await session.flush()
    await recompute_taste(session, user_id)
    await session.commit()


# The catalogue is seeded once for the whole module (the test database is remote and
# seeding takes a while); everything is rolled back when the module ends. Tests that add
# rows do so for their own new user, which leaves `me` and the recorded response alone.
pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def catalogue(migrated_test_db: None) -> AsyncIterator[AsyncSession]:
    async with rolled_back_session() as session:
        await seed_catalogue(session, CATALOGUE)
        yield session


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def world(catalogue: AsyncSession) -> tuple[AsyncSession, uuid.UUID, dict]:
    me = uuid.uuid4()
    await _rate(catalogue, me, RATED)
    catalogue.add(Dismissal(user_id=me, movie_id=DISMISSED))
    catalogue.add(WatchlistItem(user_id=me, movie_id=WATCHED, watched_at=datetime.now(UTC)))
    await catalogue.commit()
    async with api_client(catalogue) as client:
        response = await client.get("/recommendations", headers=auth(me))
    assert response.status_code == 200, response.text
    return catalogue, me, response.json()


def _items(body: dict) -> list[dict]:
    return [item for section in body["sections"] for item in section["items"]]


def _ids(body: dict) -> list[int]:
    return [item["movie"]["id"] for item in _items(body)]


async def test_sections_are_returned(world) -> None:
    _, _, body = world
    assert body["status"] == "ok"
    assert body["ratings_needed"] == 0
    keys = [section["key"] for section in body["sections"]]
    assert keys[0] == "for_you"
    assert "because_you_loved" in keys
    assert "under_90" in keys


async def test_reasons_are_recomputable_from_stored_numbers(world) -> None:
    """Every item's reasons are the rule applied to stored vectors and the catalogue's
    statistics. In this catalogue every film sits near the taste, so few or none stand
    out: an empty list is a correct answer (2026-10-02), not a missing one."""
    session, me, body = world
    user = await session.get(User, me, populate_existing=True)
    assert user is not None and user.taste_vector is not None and user.taste_weights
    rule = await load_rule(session)
    assert rule is not None
    taste = [float(v) for v in user.taste_vector]
    weights = weights_vector(user.taste_weights)
    for item in _items(body):
        film = await session.get(MovieTraits, item["movie"]["id"])
        assert film is not None
        expected = top_reasons(taste, [float(v) for v in film.vector], rule, weights=weights)
        assert item["reasons"] == expected, item["movie"]["id"]


async def test_nothing_below_the_cut(world) -> None:
    _, _, body = world
    assert all(item["match"] >= MIN_MATCH for item in _items(body))
    assert not set(_ids(body)) & {*BAD, BELOW_CUT}


async def test_rated_watched_and_dismissed_films_are_excluded(world) -> None:
    _, _, body = world
    assert not set(_ids(body)) & {*RATED, DISMISSED, WATCHED}


async def test_director_cap_holds_in_every_section(world) -> None:
    _, _, body = world
    for section in body["sections"]:
        by_auteur = [i for i in section["items"] if i["movie"]["id"] in BY_AUTEUR]
        assert len(by_auteur) <= MAX_PER_DIRECTOR, section["key"]
    # the cap bites: all four would qualify on match alone
    for_you = body["sections"][0]["items"]
    assert len([i for i in for_you if i["movie"]["id"] in BY_AUTEUR]) == MAX_PER_DIRECTOR


async def test_a_film_appears_in_one_section_only(world) -> None:
    _, _, body = world
    ids = _ids(body)
    assert len(ids) == len(set(ids))


async def test_under_90_holds_only_short_films(world) -> None:
    _, _, body = world
    (section,) = [s for s in body["sections"] if s["key"] == "under_90"]
    assert section["items"]
    assert all(item["movie"]["runtime_minutes"] <= 90 for item in section["items"])


async def test_because_you_loved_names_a_rated_film(world) -> None:
    _, _, body = world
    (section,) = [s for s in body["sections"] if s["key"] == "because_you_loved"]
    assert section["seed"]["id"] in RATED


async def test_match_is_recomputable_from_stored_numbers(world) -> None:
    """The phase-2 checklist item, automated: the API's number equals the formula's."""
    session, me, body = world
    user = await session.get(User, me, populate_existing=True)
    assert user is not None and user.taste_vector is not None and user.taste_weights
    item = _items(body)[0]
    film = await session.get(MovieTraits, item["movie"]["id"])
    assert film is not None
    expected = match_percentage(
        [float(v) for v in user.taste_vector],
        weights_vector(user.taste_weights),
        [float(v) for v in film.vector],
    )
    assert item["match"] == expected


async def test_not_enough_data_below_ten_ratings(catalogue: AsyncSession) -> None:
    me = uuid.uuid4()
    await _rate(catalogue, me, RATED[:9])
    async with api_client(catalogue) as client:
        response = await client.get("/recommendations", headers=auth(me))
    assert response.status_code == 200
    assert response.json() == {"status": "not_enough_data", "ratings_needed": 1, "sections": []}


async def test_a_new_user_needs_ten(catalogue: AsyncSession) -> None:
    async with api_client(catalogue) as client:
        response = await client.get("/recommendations", headers=auth(uuid.uuid4()))
    assert response.json()["ratings_needed"] == 10


async def test_unknown_language_is_422(catalogue: AsyncSession) -> None:
    async with api_client(catalogue) as client:
        response = await client.get("/recommendations?lang=fr", headers=auth(uuid.uuid4()))
    assert response.status_code == 422
