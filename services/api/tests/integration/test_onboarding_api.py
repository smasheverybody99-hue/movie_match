"""GET /onboarding/films: well-known films, spread over genres, not yet rated."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api import api_client, auth, seed_catalogue

DRAMA, COMEDY = (9_018, "Drama"), (9_035, "Comedy")
# Popularity decides the order inside a genre; three dramas are more popular than any
# comedy, so without the genre spread the first three would all be dramas.
FILMS = [
    {"id": 9_730_001, "genres": [DRAMA], "popularity": 90.0},
    {"id": 9_730_002, "genres": [DRAMA], "popularity": 80.0},
    {"id": 9_730_003, "genres": [DRAMA], "popularity": 70.0},
    {"id": 9_730_004, "genres": [COMEDY], "popularity": 60.0},
    {"id": 9_730_005, "genres": [COMEDY], "popularity": 50.0},
]


async def test_genres_take_turns_and_rated_films_drop_out(db_session: AsyncSession) -> None:
    await seed_catalogue(db_session, [{**f, "vector": [60.0] * 14} for f in FILMS])
    me = uuid.uuid4()
    async with api_client(db_session) as client:
        first = await client.get("/onboarding/films?limit=100", headers=auth(me))
        await client.post("/ratings", json={"movie_id": 9_730_001, "score": 8}, headers=auth(me))
        after = await client.get("/onboarding/films?limit=100", headers=auth(me))
        limited = await client.get("/onboarding/films?limit=2", headers=auth(me))

    ours = {f["id"] for f in FILMS}
    first_ids = [m["id"] for m in first.json() if m["id"] in ours]
    assert first_ids[:4] == [9_730_001, 9_730_004, 9_730_002, 9_730_005]
    assert 9_730_001 not in [m["id"] for m in after.json()]
    assert len(limited.json()) == 2


async def test_limit_is_validated(db_session: AsyncSession) -> None:
    async with api_client(db_session) as client:
        response = await client.get("/onboarding/films?limit=0", headers=auth(uuid.uuid4()))
    assert response.status_code == 422


async def test_offset_pages_through_the_same_order(db_session: AsyncSession) -> None:
    """'I have not seen any of these' asks for the next page: no film is shown twice."""
    await seed_catalogue(db_session, [{**f, "vector": [60.0] * 14} for f in FILMS])
    me = auth(uuid.uuid4())
    async with api_client(db_session) as client:
        whole = (await client.get("/onboarding/films?limit=100", headers=me)).json()
        page_1 = (await client.get("/onboarding/films?limit=2", headers=me)).json()
        page_2 = (await client.get("/onboarding/films?limit=2&offset=2", headers=me)).json()
    ids = [m["id"] for m in whole]
    assert [m["id"] for m in page_1] == ids[:2]
    assert [m["id"] for m in page_2] == ids[2:4]


async def test_offset_is_validated(db_session: AsyncSession) -> None:
    async with api_client(db_session) as client:
        response = await client.get("/onboarding/films?offset=-1", headers=auth(uuid.uuid4()))
    assert response.status_code == 422
