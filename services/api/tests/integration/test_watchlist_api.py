"""GET/POST/DELETE /watchlist and POST /watchlist/{id}/watched against the test database."""

import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WatchlistItem
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


# --- a removal racing an add or a mark (2026-10-02: POST /watchlist answered 500) ------


def _removed_by_another_request(session: AsyncSession, movie_id: int) -> None:
    """Right after the commit that stores the row, the row is deleted as if by a second
    request (the user pressed Save and then unsaved at once). The old add() committed and
    then read the row back with a separate SELECT, found nothing and answered 500.

    Earlier commits in the same request (the user row, from `current_user`) find no row
    to delete, so the hook waits for the one that does."""
    original = session.commit

    async def commit_then_delete() -> None:
        await original()
        result = await session.execute(
            delete(WatchlistItem).where(WatchlistItem.movie_id == movie_id)
        )
        await original()
        if result.rowcount:  # type: ignore[attr-defined]
            session.commit = original  # type: ignore[method-assign]

    session.commit = commit_then_delete  # type: ignore[method-assign]


async def test_an_add_racing_a_removal_answers_with_the_entry_not_500(
    seeded: AsyncSession,
) -> None:
    me = auth(uuid.uuid4())
    async with api_client(seeded) as client:
        _removed_by_another_request(seeded, A)
        added = await client.post("/watchlist", json={"movie_id": A}, headers=me)
        listed = (await client.get("/watchlist", headers=me)).json()
    assert added.status_code == 200, added.text
    assert added.json()["movie"]["id"] == A and added.json()["watched_at"] is None
    assert listed == []  # the removal came last, and it stands


async def test_adding_again_returns_the_existing_entry_unchanged(seeded: AsyncSession) -> None:
    me = auth(uuid.uuid4())
    async with api_client(seeded) as client:
        first = await client.post("/watchlist", json={"movie_id": A}, headers=me)
        watched = await client.post(f"/watchlist/{A}/watched", headers=me)
        again = await client.post("/watchlist", json={"movie_id": A}, headers=me)
    assert again.status_code == 200
    assert again.json()["added_at"] == first.json()["added_at"]
    assert again.json()["watched_at"] == watched.json()["watched_at"]  # not reset by re-adding
    rows = (await seeded.scalars(select(WatchlistItem).where(WatchlistItem.movie_id == A))).all()
    assert len(rows) == 1


async def test_marking_a_removed_film_watched_is_404_not_500(seeded: AsyncSession) -> None:
    me = auth(uuid.uuid4())
    async with api_client(seeded) as client:
        await client.post("/watchlist", json={"movie_id": A}, headers=me)
        await client.delete(f"/watchlist/{A}", headers=me)
        marked = await client.post(f"/watchlist/{A}/watched", headers=me)
    assert marked.status_code == 404
    assert marked.json()["detail"] == "Not on the watchlist"


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


async def test_rows_carry_the_personal_match(db_session: AsyncSession) -> None:
    """The same FR-5 number and band the film page shows; null for a film without traits."""
    liked, saved, unscored = 9_200_011, 9_200_012, 9_200_013
    await seed_films(db_session, {liked: [60.0] * 14, saved: [60.0] * 14, unscored: None})
    me = auth(uuid.uuid4())
    async with api_client(db_session) as client:
        empty_taste = await client.post("/watchlist", json={"movie_id": saved}, headers=me)
        await client.post("/ratings", json={"movie_id": liked, "score": 9}, headers=me)
        await client.post("/watchlist", json={"movie_id": unscored}, headers=me)
        listed = (await client.get("/watchlist", headers=me)).json()
        detail = (await client.get(f"/movies/{saved}", headers=me)).json()
    assert empty_taste.json()["match"] is None  # no taste yet when it was added
    by_id = {row["movie"]["id"]: row["match"] for row in listed}
    assert by_id == {saved: 100, unscored: None}  # identical vectors: a 100% match
    assert detail["match"] == by_id[saved]
    # A 100% match is at place 1 of any catalogue: always "strong", here and on the page.
    bands = {row["movie"]["id"]: row["band"] for row in listed}
    assert bands == {saved: "strong", unscored: None}
    assert detail["band"] == "strong"
