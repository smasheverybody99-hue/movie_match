"""POST /dismissals and DELETE /dismissals/{movie_id}."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Dismissal
from tests.integration.api import api_client, auth, seed_films

FILM = 9_710_001


async def _count(session: AsyncSession, user_id: uuid.UUID) -> int:
    return await session.scalar(  # type: ignore[return-value]
        select(func.count()).select_from(Dismissal).where(Dismissal.user_id == user_id)
    )


async def test_dismiss_twice_then_undo(db_session: AsyncSession) -> None:
    await seed_films(db_session, {FILM: None})
    me = uuid.uuid4()
    async with api_client(db_session) as client:
        for _ in range(2):
            response = await client.post("/dismissals", json={"movie_id": FILM}, headers=auth(me))
            assert response.status_code == 204
        assert await _count(db_session, me) == 1
        assert (await client.delete(f"/dismissals/{FILM}", headers=auth(me))).status_code == 204
        assert (await client.delete(f"/dismissals/{FILM}", headers=auth(me))).status_code == 404
    assert await _count(db_session, me) == 0


async def test_unknown_film_is_404(db_session: AsyncSession) -> None:
    async with api_client(db_session) as client:
        response = await client.post(
            "/dismissals", json={"movie_id": 1}, headers=auth(uuid.uuid4())
        )
    assert response.status_code == 404


async def test_invalid_input_is_422(db_session: AsyncSession) -> None:
    async with api_client(db_session) as client:
        response = await client.post(
            "/dismissals", json={"movie_id": 0}, headers=auth(uuid.uuid4())
        )
        assert response.status_code == 422
        response = await client.delete("/dismissals/-5", headers=auth(uuid.uuid4()))
        assert response.status_code == 422
