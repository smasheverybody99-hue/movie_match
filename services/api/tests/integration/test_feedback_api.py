"""POST /feedback: "this recommendation was wrong", with an optional reason (Phase 5)."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RecommendationFeedback
from tests.integration.api import api_client, auth, seed_catalogue

LIKED = list(range(9_820_101, 9_820_111))  # ten: recommendations need ten ratings (FR-3)
FILMS = [9_820_002, 9_820_003, 9_820_004]


@pytest.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed_catalogue(
        db_session,
        [{"id": m, "vector": [70.0] * 14} for m in LIKED]
        + [{"id": f, "vector": [70.0 - i] * 14} for i, f in enumerate(FILMS)],
    )
    return db_session


async def _rows(session: AsyncSession, user_id: uuid.UUID) -> list[tuple]:
    session.expire_all()
    rows = await session.scalars(
        select(RecommendationFeedback).where(RecommendationFeedback.user_id == user_id)
    )
    return [(r.movie_id, r.source, r.reason) for r in rows.all()]


async def test_a_press_is_stored_and_a_second_replaces_it(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    film = FILMS[0]
    async with api_client(seeded) as client:
        first = await client.post(
            "/feedback", json={"movie_id": film, "source": "for_you"}, headers=auth(me)
        )
        assert first.status_code == 204, first.text
        assert await _rows(seeded, me) == [(film, "for_you", None)]
        again = await client.post(
            "/feedback",
            json={"movie_id": film, "source": "assistant", "reason": "too_old"},
            headers=auth(me),
        )
    assert again.status_code == 204
    assert await _rows(seeded, me) == [(film, "assistant", "too_old")]


@pytest.mark.parametrize("reason", ["seen", "not_my_genre", "too_old", "other"])
async def test_each_chip_is_a_reason(seeded: AsyncSession, reason: str) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        response = await client.post(
            "/feedback",
            json={"movie_id": FILMS[1], "source": "under_90", "reason": reason},
            headers=auth(me),
        )
    assert response.status_code == 204
    assert await _rows(seeded, me) == [(FILMS[1], "under_90", reason)]


async def test_it_does_not_change_the_recommendations(seeded: AsyncSession) -> None:
    """Data, not a ranking input: the film stays where it was (TZ 1.31, no change mid-alpha)."""
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        for movie_id in LIKED:
            await client.post("/ratings", json={"movie_id": movie_id, "score": 9}, headers=auth(me))
        before = (await client.get("/recommendations", headers=auth(me))).json()
        await client.post(
            "/feedback", json={"movie_id": FILMS[0], "source": "for_you"}, headers=auth(me)
        )
        after = (await client.get("/recommendations", headers=auth(me))).json()
    assert before["status"] == "ok"
    assert FILMS[0] in {i["movie"]["id"] for s in before["sections"] for i in s["items"]}
    assert after == before


async def test_a_film_not_in_the_catalogue_is_404(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        response = await client.post(
            "/feedback",
            json={"movie_id": 999_999_996, "source": "for_you"},
            headers=auth(uuid.uuid4()),
        )
    assert response.status_code == 404
    assert response.json() == {"detail": "Movie not found"}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"movie_id": FILMS[0]},  # no source
        {"movie_id": 0, "source": "for_you"},
        {"movie_id": FILMS[0], "source": "search"},
        {"movie_id": FILMS[0], "source": "for_you", "reason": "boring"},
        {"movie_id": FILMS[0], "source": "for_you", "note": "I hate this film"},  # no free text
    ],
)
async def test_invalid_input_is_422(seeded: AsyncSession, body: dict) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        response = await client.post("/feedback", json=body, headers=auth(me))
    assert response.status_code == 422
    assert await _rows(seeded, me) == []


async def test_missing_and_forged_tokens_are_401(seeded: AsyncSession) -> None:
    body = {"movie_id": FILMS[0], "source": "for_you"}
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        missing = await client.post("/feedback", json=body)
        forged = await client.post("/feedback", json=body, headers=auth(me, forged=True))
    assert (missing.status_code, forged.status_code) == (401, 401)
    assert await _rows(seeded, me) == []
