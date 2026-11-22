"""Sensitive films (Phase 5, NSFW): in no list, and the film page says what they are.

The sensitive film here has the very taste of the viewer, so any list that let it
through would put it first.
"""

import uuid

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie, TraitFailure
from app.pipelines import sensitive
from app.services import recommend
from app.services.recommend import SearchRequest
from tests.integration.api import api_client, auth, seed_catalogue

LIKED = list(range(9_830_101, 9_830_111))  # ten: recommendations need ten ratings (FR-3)
PLAIN, EXPLICIT = 9_830_001, 9_830_002
# Weaker films, so the floor cut (the lowest match_floor_share of the catalogue) falls on
# them and not on PLAIN: with only these twelve films PLAIN would be the lowest and dropped.
FILLER = list(range(9_830_011, 9_830_017))


@pytest.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed_catalogue(
        db_session,
        [{"id": m, "vector": [70.0] * 14, "popularity": 1.0} for m in LIKED]
        + [
            {"id": PLAIN, "vector": [69.0] * 14, "popularity": 50.0},
            {"id": EXPLICIT, "vector": [70.0] * 14, "popularity": 99.0},
        ]
        + [{"id": m, "vector": [30.0] * 14} for m in FILLER],
    )
    await db_session.execute(update(Movie).where(Movie.id == EXPLICIT).values(sensitive=True))
    await db_session.commit()
    return db_session


async def _viewer(client, me: dict[str, str]) -> None:
    for movie_id in LIKED:
        await client.post("/ratings", json={"movie_id": movie_id, "score": 9}, headers=me)


async def test_search_leaves_it_out(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        found = (await client.get("/movies", params={"q": "Film 98300", "limit": 50})).json()
    ids = {m["id"] for m in found}
    assert PLAIN in ids and EXPLICIT not in ids


async def test_onboarding_leaves_it_out(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        films = (await client.get("/onboarding/films?limit=100", headers=auth(uuid.uuid4()))).json()
    ids = {m["id"] for m in films}
    assert EXPLICIT not in ids


async def test_recommendations_leave_it_out(seeded: AsyncSession) -> None:
    me = auth(uuid.uuid4())
    async with api_client(seeded) as client:
        await _viewer(client, me)
        feed = (await client.get("/recommendations", headers=me)).json()
    assert feed["status"] == "ok"
    ids = {i["movie"]["id"] for s in feed["sections"] for i in s["items"]}
    assert PLAIN in ids and EXPLICIT not in ids


async def test_the_assistant_search_leaves_it_out(seeded: AsyncSession) -> None:
    user = uuid.uuid4()
    async with api_client(seeded) as client:
        await _viewer(client, auth(user))
    result = await recommend.search(seeded, user, SearchRequest())
    ids = {hit.movie.id for hit in result.hits}
    assert PLAIN in ids and EXPLICIT not in ids


async def test_the_page_says_it_is_sensitive(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        explicit = (await client.get(f"/movies/{EXPLICIT}")).json()
        plain = (await client.get(f"/movies/{PLAIN}")).json()
    assert (explicit["sensitive"], plain["sensitive"]) == (True, False)


async def test_the_command_marks_refused_and_listed_films(db_session: AsyncSession) -> None:
    hand = next(iter(sensitive.HAND_LIST))
    refused, other_error, untouched = 9_830_201, 9_830_202, 9_830_203
    await seed_catalogue(
        db_session,
        [{"id": i, "vector": [50.0] * 14} for i in (hand, refused, other_error, untouched)],
    )
    db_session.add_all(
        [
            TraitFailure(
                movie_id=refused,
                attempts=2,
                last_error="no candidates (prompt blocked: BlockedReason.PROHIBITED_CONTENT)",
            ),
            TraitFailure(movie_id=other_error, attempts=2, last_error="timeout"),
        ]
    )
    await db_session.commit()

    found = {movie_id for movie_id, _, _ in await sensitive.candidates(db_session)}
    assert {hand, refused} <= found
    assert other_error not in found and untouched not in found

    assert await sensitive.mark(db_session, sorted(found)) >= 2
    assert await sensitive.mark(db_session, sorted(found)) == 0  # already marked
    marked = set(
        (await db_session.scalars(select(Movie.id).where(Movie.sensitive.is_(True)))).all()
    )
    assert {hand, refused} <= marked and untouched not in marked
