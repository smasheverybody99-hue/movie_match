"""User A can neither see nor change user B's ratings or watchlist."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rating, WatchlistItem
from tests.integration.api import api_client, auth, seed_films

FILM = 9_400_001


@pytest.fixture
async def two_users(db_session: AsyncSession) -> tuple[AsyncSession, uuid.UUID, uuid.UUID]:
    await seed_films(db_session, {FILM: [70.0] * 14})
    alice, bob = uuid.uuid4(), uuid.uuid4()
    async with api_client(db_session) as client:
        await client.post("/ratings", json={"movie_id": FILM, "score": 9}, headers=auth(bob))
        await client.post("/watchlist", json={"movie_id": FILM}, headers=auth(bob))
    return db_session, alice, bob


async def test_a_user_sees_only_their_own_rows(two_users) -> None:
    session, alice, _ = two_users
    async with api_client(session) as client:
        assert (await client.get("/ratings", headers=auth(alice))).json() == []
        assert (await client.get("/watchlist", headers=auth(alice))).json() == []


async def test_a_user_cannot_delete_or_mark_anothers_rows(two_users) -> None:
    session, alice, bob = two_users
    async with api_client(session) as client:
        assert (await client.delete(f"/ratings/{FILM}", headers=auth(alice))).status_code == 404
        assert (await client.delete(f"/watchlist/{FILM}", headers=auth(alice))).status_code == 404
        marked = await client.post(f"/watchlist/{FILM}/watched", headers=auth(alice))
        assert marked.status_code == 404

    rating = await session.scalar(
        select(Rating).where(Rating.user_id == bob).execution_options(populate_existing=True)
    )
    item = await session.scalar(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == bob)
        .execution_options(populate_existing=True)
    )
    assert rating is not None and rating.score == 9.0
    assert item is not None and item.watched_at is None


async def test_rating_the_same_film_does_not_touch_anothers_rating(two_users) -> None:
    session, alice, bob = two_users
    async with api_client(session) as client:
        await client.post("/ratings", json={"movie_id": FILM, "score": 2}, headers=auth(alice))
        bobs = (await client.get("/ratings", headers=auth(bob))).json()
    assert [(r["movie_id"], r["score"]) for r in bobs] == [(FILM, 9.0)]
