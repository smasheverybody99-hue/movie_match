"""GET/POST/DELETE /watchlist and POST /watchlist/{id}/watched against the test database."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api import api_client, auth, seed_films

A, B = 9_200_001, 9_200_002


@pytest.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed_films(db_session, {A: None, B: None})
    return db_session


async def test_add_list_mark_watched_remove(seeded: AsyncSession) -> None:
    me = auth(uuid.uuid4())
    async with api_client(seeded) as client:
        assert (await client.get("/watchlist", headers=me)).json() == []

        added = await client.post("/watchlist", json={"movie_id": A}, headers=me)
        assert added.status_code == 200, added.text
        assert added.json()["movie"]["id"] == A
        assert added.json()["movie"]["title"] == f"Film {A}"
        assert added.json()["watched_at"] is None

        await client.post("/watchlist", json={"movie_id": B}, headers=me)
        watched = await client.post(f"/watchlist/{A}/watched", headers=me)
        assert watched.status_code == 200
        assert watched.json()["watched_at"] is not None

        listed = (await client.get("/watchlist", headers=me)).json()
        assert [i["movie"]["id"] for i in listed] == [B, A]  # unwatched first

        removed = await client.delete(f"/watchlist/{B}", headers=me)
        assert removed.status_code == 204
        assert [i["movie"]["id"] for i in (await client.get("/watchlist", headers=me)).json()] == [
            A
        ]


async def test_adding_twice_keeps_one_entry(seeded: AsyncSession) -> None:
    me = auth(uuid.uuid4())
    async with api_client(seeded) as client:
        first = await client.post("/watchlist", json={"movie_id": A}, headers=me)
        second = await client.post("/watchlist", json={"movie_id": A}, headers=me)
        listed = (await client.get("/watchlist", headers=me)).json()
    assert second.status_code == 200
    assert second.json()["added_at"] == first.json()["added_at"]
    assert len(listed) == 1


async def test_marking_watched_again_keeps_the_first_date(seeded: AsyncSession) -> None:
    me = auth(uuid.uuid4())
    async with api_client(seeded) as client:
        await client.post("/watchlist", json={"movie_id": A}, headers=me)
        first = await client.post(f"/watchlist/{A}/watched", headers=me)
        again = await client.post(f"/watchlist/{A}/watched", headers=me)
    assert again.json()["watched_at"] == first.json()["watched_at"]


# --- not found ----------------------------------------------------------------------


async def test_adding_a_film_not_in_the_catalogue_is_404(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        response = await client.post(
            "/watchlist", json={"movie_id": 999_999_999}, headers=auth(uuid.uuid4())
        )
    assert response.status_code == 404
    assert response.json() == {"detail": "Movie not found"}


@pytest.mark.parametrize(
    ("method", "path"), [("DELETE", f"/watchlist/{A}"), ("POST", f"/watchlist/{A}/watched")]
)
async def test_a_film_not_on_the_list_is_404(seeded: AsyncSession, method: str, path: str) -> None:
    async with api_client(seeded) as client:
        response = await client.request(method, path, headers=auth(uuid.uuid4()))
    assert response.status_code == 404
    assert response.json() == {"detail": "Not on the watchlist"}


# --- invalid input ------------------------------------------------------------------


@pytest.mark.parametrize("body", [{}, {"movie_id": 0}, {"movie_id": "abc"}])
async def test_invalid_add_is_422(seeded: AsyncSession, body: dict) -> None:
    async with api_client(seeded) as client:
        response = await client.post("/watchlist", json=body, headers=auth(uuid.uuid4()))
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("method", "path"),
    [("DELETE", "/watchlist/abc"), ("POST", "/watchlist/abc/watched"), ("DELETE", "/watchlist/0")],
)
async def test_invalid_movie_id_in_path_is_422(
    seeded: AsyncSession, method: str, path: str
) -> None:
    async with api_client(seeded) as client:
        response = await client.request(method, path, headers=auth(uuid.uuid4()))
    assert response.status_code == 422
