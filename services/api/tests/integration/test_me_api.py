"""GET /me: the caller's account summary."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api import api_client, auth, seed_films

FILMS = [9_720_001, 9_720_002]


async def test_a_new_user(db_session: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(db_session) as client:
        body = (await client.get("/me", headers=auth(me))).json()
    assert body["id"] == str(me)
    assert body["rating_count"] == 0
    assert body["ratings_needed"] == 10
    assert body["has_taste_profile"] is False
    assert body["taste_updated_at"] is None


async def test_after_two_ratings(db_session: AsyncSession) -> None:
    await seed_films(db_session, {m: [70.0] * 14 for m in FILMS})
    me = uuid.uuid4()
    async with api_client(db_session) as client:
        for movie_id in FILMS:
            await client.post("/ratings", json={"movie_id": movie_id, "score": 9}, headers=auth(me))
        body = (await client.get("/me", headers=auth(me))).json()
    assert body["rating_count"] == 2
    assert body["ratings_needed"] == 8
    assert body["has_taste_profile"] is True
    assert body["taste_updated_at"]
