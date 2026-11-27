"""DELETE /me removes the whole account (Phase 9a, required test).

Every table that references users.id is found from the schema itself, so a table added
later is covered without editing this file - and the test fails until it is seeded here.
The Supabase sign-in record (`auth.users`) must go too. The CI database is plain Postgres
without the `auth` schema, so a minimal stand-in is created inside the test's transaction
(it is rolled back with everything else); on a Supabase test database the real table is
used.
"""

import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AssistantTurn,
    AssistantUsage,
    Base,
    Dismissal,
    Event,
    Explanation,
    Rating,
    RecommendationFeedback,
    User,
    WatchlistItem,
)
from app.services import users
from tests.integration.api import api_client, auth, seed_films

FILMS = [9_710_001, 9_710_002]


def _user_tables() -> set[str]:
    """Every table with a foreign key to users.id."""
    return {
        table.name
        for table in Base.metadata.sorted_tables
        for fk in table.foreign_keys
        if fk.column.table.name == "users" and fk.column.name == "id"
    }


def _rows(user_id: uuid.UUID) -> list[object]:
    now = datetime.now(UTC)
    return [
        Rating(user_id=user_id, movie_id=FILMS[0], score=8.0, liked_aspects=["humor"]),
        WatchlistItem(user_id=user_id, movie_id=FILMS[1]),
        Explanation(user_id=user_id, movie_id=FILMS[0], lang="en", text="x", model="m"),
        AssistantTurn(user_id=user_id, question="q", answer="a", movie_ids=[FILMS[0]]),
        AssistantUsage(user_id=user_id, day=date(2026, 11, 27), calls=1),
        Event(user_id=user_id, type="onboarding_step", props={}, occurred_at=now),
        RecommendationFeedback(user_id=user_id, movie_id=FILMS[1], source="for_you"),
        Dismissal(user_id=user_id, movie_id=FILMS[1]),
    ]


async def _ensure_auth_users(session: AsyncSession) -> bool:
    """Make `auth.users` exist. True when it is a stand-in this test created."""
    if await users.has_auth_schema(session):
        return False
    await session.execute(text("CREATE SCHEMA auth"))
    await session.execute(text("CREATE TABLE auth.users (id uuid PRIMARY KEY, email text)"))
    return True


async def _count(session: AsyncSession, table: str, user_id: uuid.UUID) -> int:
    column = "id" if table in {"users", "auth.users"} else "user_id"
    result = await session.scalar(
        text(f"SELECT count(*) FROM {table} WHERE {column} = :id"),  # table names are fixed
        {"id": user_id},
    )
    return int(result or 0)


async def _seed(session: AsyncSession, user_id: uuid.UUID, email: str) -> None:
    await session.execute(
        text("INSERT INTO auth.users (id, email) VALUES (:id, :email)"),
        {"id": user_id, "email": email},
    )
    session.add(User(id=user_id))
    await session.flush()
    session.add_all(_rows(user_id))
    await session.commit()


async def test_every_user_table_is_seeded_here() -> None:
    """A new user table must be added to _rows, so that the deletion test covers it."""
    seeded = {type(row).__table__.name for row in _rows(uuid.uuid4())}  # type: ignore[attr-defined]
    assert seeded == _user_tables()


async def test_delete_removes_every_row_and_the_sign_in_record(db_session: AsyncSession) -> None:
    await seed_films(db_session, {m: [60.0] * 14 for m in FILMS})
    await _ensure_auth_users(db_session)
    me, other = uuid.uuid4(), uuid.uuid4()
    await _seed(db_session, me, f"{me.hex}@example.invalid")
    await _seed(db_session, other, f"{other.hex}@example.invalid")
    tables = ["users", "auth.users", *sorted(_user_tables())]
    for table in tables:
        assert await _count(db_session, table, me) == 1, table

    async with api_client(db_session) as client:
        response = await client.delete("/me", headers=auth(me))
    assert response.status_code == 204

    db_session.expunge_all()
    for table in tables:
        assert await _count(db_session, table, me) == 0, table
        assert await _count(db_session, table, other) == 1, f"{table} (someone else's)"


async def test_nothing_is_deleted_when_the_sign_in_record_cannot_be(
    db_session: AsyncSession,
) -> None:
    """One transaction: a failure on auth.users leaves the app's rows in place."""
    if not await _ensure_auth_users(db_session):
        pytest.skip("a real auth.users: no failing trigger is put on it")
    await db_session.execute(
        text(
            "CREATE FUNCTION auth.refuse() RETURNS trigger LANGUAGE plpgsql AS "
            "$$ BEGIN RAISE EXCEPTION 'refused'; END $$"
        )
    )
    await db_session.execute(
        text(
            "CREATE TRIGGER refuse BEFORE DELETE ON auth.users "
            "FOR EACH ROW EXECUTE FUNCTION auth.refuse()"
        )
    )
    await seed_films(db_session, {m: [60.0] * 14 for m in FILMS})
    me = uuid.uuid4()
    await _seed(db_session, me, "x@example.invalid")

    with pytest.raises(DBAPIError):
        await users.delete_user(db_session, me)
    await db_session.rollback()

    db_session.expunge_all()
    assert await db_session.scalar(select(func.count()).select_from(User).where(User.id == me)) == 1
    assert await _count(db_session, "ratings", me) == 1
    assert await _count(db_session, "auth.users", me) == 1


async def test_without_an_auth_schema_the_app_rows_still_go(db_session: AsyncSession) -> None:
    """Local and CI databases have no auth schema: deletion must not fail there."""
    if await users.has_auth_schema(db_session):
        pytest.skip("this database has an auth schema")
    await seed_films(db_session, {m: [60.0] * 14 for m in FILMS})
    me = uuid.uuid4()
    db_session.add(User(id=me))
    await db_session.flush()
    db_session.add_all(_rows(me))
    await db_session.commit()

    await users.delete_user(db_session, me)

    for table in ["users", *sorted(_user_tables())]:
        assert await _count(db_session, table, me) == 0, table
