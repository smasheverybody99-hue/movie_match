"""POST/GET/DELETE /ratings against the test database, and the taste profile they drive."""

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rating, User
from app.traits import TRAIT_COUNT, TRAIT_KEYS
from tests.integration.api import api_client, auth, seed_films

HIGH = [80.0] * TRAIT_COUNT
LOW = [20.0] * TRAIT_COUNT
FILMS = {9_100_001: HIGH, 9_100_002: LOW, 9_100_003: None}  # the third has no traits yet


@pytest.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed_films(db_session, FILMS)
    return db_session


async def _user(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id, populate_existing=True)
    assert user is not None
    return user


async def test_rate_creates_the_user_and_the_rating(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        response = await client.post(
            "/ratings",
            json={"movie_id": 9_100_001, "score": 9.0, "liked_aspects": ["plot_twist"]},
            headers=auth(me),
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["movie_id"] == 9_100_001
    assert body["score"] == 9.0
    assert body["liked_aspects"] == ["plot_twist"]
    assert body["rated_at"]
    assert await seeded.get(User, me) is not None


async def test_rating_twice_updates_rather_than_duplicates(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        await client.post("/ratings", json={"movie_id": 9_100_001, "score": 6}, headers=auth(me))
        again = await client.post(
            "/ratings", json={"movie_id": 9_100_001, "score": 9.5}, headers=auth(me)
        )
        listed = await client.get("/ratings", headers=auth(me))

    assert again.status_code == 200
    count = await seeded.scalar(
        select(func.count()).select_from(Rating).where(Rating.user_id == me)
    )
    assert count == 1
    assert [(r["movie_id"], r["score"]) for r in listed.json()] == [(9_100_001, 9.5)]


async def test_taste_vector_follows_the_ratings(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        await client.post("/ratings", json={"movie_id": 9_100_001, "score": 9}, headers=auth(me))
        user = await _user(seeded, me)
        # one liked film at 80 everywhere: the taste is that film
        assert list(user.taste_vector) == pytest.approx(HIGH)
        assert set(user.taste_weights) == set(TRAIT_KEYS)
        assert user.taste_weights[TRAIT_KEYS[0]] == pytest.approx(0.625)  # one favourite
        first_update = user.taste_updated_at

        await client.post("/ratings", json={"movie_id": 9_100_002, "score": 7}, headers=auth(me))
        user = await _user(seeded, me)
        # weights 9 - 5 = 4 and 7 - 5 = 2 (same day): (4·80 + 2·20) / 6 = 60
        assert list(user.taste_vector) == pytest.approx([60.0] * TRAIT_COUNT)
        assert user.taste_updated_at >= first_update

        await client.delete("/ratings/9100001", headers=auth(me))
        user = await _user(seeded, me)
        assert list(user.taste_vector) == pytest.approx(LOW)


async def test_rating_an_unscored_film_is_kept_but_adds_no_taste(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        response = await client.post(
            "/ratings", json={"movie_id": 9_100_003, "score": 10}, headers=auth(me)
        )
    assert response.status_code == 200
    user = await _user(seeded, me)
    assert user.taste_vector is None and user.taste_weights is None
    assert user.taste_updated_at is not None


async def test_only_disliked_films_leave_no_taste(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        await client.post("/ratings", json={"movie_id": 9_100_001, "score": 3}, headers=auth(me))
    assert (await _user(seeded, me)).taste_vector is None


async def test_delete_removes_the_rating(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        await client.post("/ratings", json={"movie_id": 9_100_001, "score": 8}, headers=auth(me))
        deleted = await client.delete("/ratings/9100001", headers=auth(me))
        listed = await client.get("/ratings", headers=auth(me))
    assert deleted.status_code == 204
    assert listed.json() == []
    assert (await _user(seeded, me)).taste_vector is None


async def test_list_is_newest_first_and_empty_for_a_new_user(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        assert (await client.get("/ratings", headers=auth(me))).json() == []
        await client.post("/ratings", json={"movie_id": 9_100_001, "score": 8}, headers=auth(me))
        await client.post("/ratings", json={"movie_id": 9_100_002, "score": 4}, headers=auth(me))
        listed = await client.get("/ratings", headers=auth(me))
    # both written in one test transaction, so the timestamps tie and movie id decides
    assert [r["movie_id"] for r in listed.json()] == [9_100_001, 9_100_002]


# --- not found ----------------------------------------------------------------------


async def test_rating_a_film_not_in_the_catalogue_is_404(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        response = await client.post(
            "/ratings", json={"movie_id": 999_999_999, "score": 8}, headers=auth(uuid.uuid4())
        )
    assert response.status_code == 404
    assert response.json() == {"detail": "Movie not found"}


async def test_deleting_a_rating_that_does_not_exist_is_404(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        response = await client.delete("/ratings/9100001", headers=auth(uuid.uuid4()))
    assert response.status_code == 404
    assert response.json() == {"detail": "Rating not found"}


# --- invalid input ------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        {"movie_id": 9_100_001, "score": 0.0},  # below 0.5
        {"movie_id": 9_100_001, "score": 10.5},  # above 10
        {"movie_id": 9_100_001},  # no score
        {"movie_id": -1, "score": 8},
        {"movie_id": "abc", "score": 8},
        {"movie_id": 9_100_001, "score": 9, "liked_aspects": ["not_a_trait"]},
        {"movie_id": 9_100_001, "score": 9, "liked_aspects": ["humor", "humor"]},
    ],
    ids=["too-low", "too-high", "no-score", "negative-id", "text-id", "bad-aspect", "repeat"],
)
async def test_invalid_rating_is_422(seeded: AsyncSession, body: dict) -> None:
    async with api_client(seeded) as client:
        response = await client.post("/ratings", json=body, headers=auth(uuid.uuid4()))
    assert response.status_code == 422


@pytest.mark.parametrize("path", ["/ratings/abc", "/ratings/0"])
async def test_invalid_movie_id_in_path_is_422(seeded: AsyncSession, path: str) -> None:
    async with api_client(seeded) as client:
        response = await client.delete(path, headers=auth(uuid.uuid4()))
    assert response.status_code == 422
