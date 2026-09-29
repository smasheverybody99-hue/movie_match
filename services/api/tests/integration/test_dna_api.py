"""GET /me/dna: the caller's taste vector by trait, and their rating stats (FR-7)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.traits import TRAIT_KEYS
from tests.integration.api import api_client, auth, seed_catalogue

DRAMA, COMEDY = (9_018, "Drama"), (9_035, "Comedy")
FILMS = [9_770_001 + i for i in range(10)]


async def test_a_new_user_needs_ten_ratings(db_session: AsyncSession) -> None:
    async with api_client(db_session) as client:
        response = await client.get("/me/dna", headers=auth(uuid.uuid4()))
    assert response.status_code == 200, response.text
    assert response.json() == {
        "scores": {},
        "summary": None,
        "rating_count": 0,
        "ratings_needed": 10,
        "average_rating": None,
        "top_genre": None,
    }


async def test_after_ten_ratings(db_session: AsyncSession) -> None:
    # Seven dramas and three comedies: drama is the top genre.
    await seed_catalogue(
        db_session,
        [
            {"id": m, "vector": [40.0 + i] * 14, "genres": [DRAMA] if i < 7 else [COMEDY]}
            for i, m in enumerate(FILMS)
        ],
    )
    me = uuid.uuid4()
    async with api_client(db_session) as client:
        for i, movie_id in enumerate(FILMS):
            score = 9.0 if i < 5 else 4.0
            await client.post(
                "/ratings", json={"movie_id": movie_id, "score": score}, headers=auth(me)
            )
        body = (await client.get("/me/dna", headers=auth(me))).json()

    assert body["rating_count"] == 10
    assert body["ratings_needed"] == 0
    assert body["average_rating"] == 6.5  # (5·9 + 5·4) / 10
    assert body["top_genre"] == "Drama"
    assert list(body["scores"]) == list(TRAIT_KEYS)  # vector order
    # The scores are users.taste_vector, rounded to one decimal - nothing else.
    user = await db_session.get(User, me, populate_existing=True)
    assert user is not None and user.taste_vector is not None
    assert body["scores"] == {
        key: round(float(v), 1) for key, v in zip(TRAIT_KEYS, user.taste_vector, strict=True)
    }
    # Only the five films rated 9 (vectors 40..44, equal weight) pull the taste: mean 42.
    assert body["scores"]["darkness"] == 42.0


async def test_genre_ties_go_to_the_first_name(db_session: AsyncSession) -> None:
    await seed_catalogue(
        db_session,
        [
            {"id": FILMS[0], "vector": [50.0] * 14, "genres": [DRAMA]},
            {"id": FILMS[1], "vector": [50.0] * 14, "genres": [COMEDY]},
        ],
    )
    me = uuid.uuid4()
    async with api_client(db_session) as client:
        for movie_id in FILMS[:2]:
            await client.post("/ratings", json={"movie_id": movie_id, "score": 7}, headers=auth(me))
        body = (await client.get("/me/dna", headers=auth(me))).json()
    assert body["top_genre"] == "Comedy"
    assert body["ratings_needed"] == 8
