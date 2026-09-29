"""DELETE /me: afterwards no row in any user table belongs to that user."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Dismissal, Explanation, Rating, User, WatchlistItem
from tests.integration.api import api_client, auth, seed_films

FILMS = [9_700_001, 9_700_002, 9_700_003]
USER_TABLES = [Rating, WatchlistItem, Dismissal, Explanation]


async def _count(session: AsyncSession, model: type, user_id: uuid.UUID) -> int:
    column = model.id if model is User else model.user_id  # type: ignore[attr-defined]
    return await session.scalar(select(func.count()).select_from(model).where(column == user_id))  # type: ignore[return-value]


async def test_no_rows_remain_after_delete(db_session: AsyncSession) -> None:
    await seed_films(db_session, {m: [70.0] * 14 for m in FILMS})
    me, other = uuid.uuid4(), uuid.uuid4()
    async with api_client(db_session) as client:
        for user in (me, other):
            await client.post(
                "/ratings", json={"movie_id": FILMS[0], "score": 9}, headers=auth(user)
            )
            await client.post("/watchlist", json={"movie_id": FILMS[1]}, headers=auth(user))
            await client.post("/dismissals", json={"movie_id": FILMS[2]}, headers=auth(user))
        db_session.add(Explanation(user_id=me, movie_id=FILMS[0], lang="uz", text="x", model="m"))
        await db_session.commit()
        for model in USER_TABLES:
            assert await _count(db_session, model, me) == 1, model.__name__

        response = await client.delete("/me", headers=auth(me))
    assert response.status_code == 204

    db_session.expunge_all()
    assert await _count(db_session, User, me) == 0
    for model in USER_TABLES:
        assert await _count(db_session, model, me) == 0, model.__name__
    # someone else's data is untouched
    for model in (User, Rating, WatchlistItem, Dismissal):
        assert await _count(db_session, model, other) == 1, model.__name__


async def test_deleting_twice_is_harmless(db_session: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(db_session) as client:
        assert (await client.delete("/me", headers=auth(me))).status_code == 204
        assert (await client.delete("/me", headers=auth(me))).status_code == 204
