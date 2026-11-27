"""GET /me/export: everything the app holds for the caller (Phase 9a, required test).

The export must contain every table holding the user's data - found here from the schema,
so a table added later fails this test until the export and the seed below cover it -
and a new user with no data gets a valid, empty export.
"""

import json
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import text
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
from app.services import export
from tests.integration.api import api_client, auth, seed_films

FILMS = [9_720_001, 9_720_002, 9_720_003]


def _schema_user_tables() -> set[str]:
    return {"users"} | {
        table.name
        for table in Base.metadata.sorted_tables
        for fk in table.foreign_keys
        if fk.column.table.name == "users" and fk.column.name == "id"
    }


def _rows(user_id: uuid.UUID) -> list[object]:
    now = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)
    return [
        Rating(user_id=user_id, movie_id=FILMS[0], score=8.5, liked_aspects=["humor"]),
        WatchlistItem(user_id=user_id, movie_id=FILMS[1], watched_at=now),
        Explanation(user_id=user_id, movie_id=FILMS[0], lang="en", text="Funny.", model="m"),
        AssistantTurn(user_id=user_id, question="q?", answer="a.", movie_ids=[FILMS[2]]),
        AssistantUsage(user_id=user_id, day=date(2026, 11, 27), calls=3),
        Event(
            user_id=user_id,
            type="recommendation_shown",
            movie_id=FILMS[1],
            source="for_you",
            props={},
            occurred_at=now,
        ),
        RecommendationFeedback(user_id=user_id, movie_id=FILMS[1], source="for_you", reason="seen"),
        Dismissal(user_id=user_id, movie_id=FILMS[2]),
    ]


async def _seed(session: AsyncSession, user_id: uuid.UUID) -> None:
    session.add(User(id=user_id, taste_vector=[50.0] * 14))
    await session.flush()
    session.add_all(_rows(user_id))
    await session.commit()


def test_the_export_covers_every_user_table() -> None:
    exported = {table.name for table, _ in export.user_tables()}
    assert exported == _schema_user_tables()
    seeded = {type(row).__table__.name for row in _rows(uuid.uuid4())}  # type: ignore[attr-defined]
    assert seeded | {"users"} == _schema_user_tables(), "seed a row for the new table here"


async def test_export_holds_every_row_of_mine_and_none_of_theirs(
    db_session: AsyncSession,
) -> None:
    await seed_films(db_session, {m: [60.0] * 14 for m in FILMS})
    me, other = uuid.uuid4(), uuid.uuid4()
    await _seed(db_session, me)
    await _seed(db_session, other)

    async with api_client(db_session) as client:
        response = await client.get("/me/export", headers=auth(me))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()

    assert body["format"] == "movie-match-export/1"
    assert body["user_id"] == str(me)
    assert set(body["tables"]) == _schema_user_tables()
    for name, rows in body["tables"].items():
        assert len(rows) == 1, name
        owner = rows[0]["id"] if name == "users" else rows[0]["user_id"]
        assert owner == str(me), name
    assert body["tables"]["ratings"][0]["score"] == 8.5
    assert body["tables"]["ratings"][0]["liked_aspects"] == ["humor"]
    assert body["tables"]["users"][0]["taste_vector"] == [50.0] * 14
    assert body["tables"]["assistant_turns"][0]["question"] == "q?"
    assert body["tables"]["assistant_usage"][0]["day"] == "2026-11-27"
    assert body["movies"] == {str(m): f"Film {m}" for m in FILMS}
    assert str(other) not in json.dumps(body)


async def test_a_new_user_gets_a_valid_empty_export(db_session: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(db_session) as client:
        response = await client.get("/me/export", headers=auth(me))
    assert response.status_code == 200
    body = response.json()
    assert set(body["tables"]) == _schema_user_tables()
    # The users row is created on first sight of the token; everything else is empty.
    assert [row["id"] for row in body["tables"]["users"]] == [str(me)]
    assert all(rows == [] for name, rows in body["tables"].items() if name != "users")
    assert body["movies"] == {}


async def test_the_sign_in_record_is_in_the_export(db_session: AsyncSession) -> None:
    """The email lives in Supabase's auth.users. CI has no auth schema: a stand-in is made
    inside the test's transaction; on a Supabase test database the real table is used."""
    if not await db_session.scalar(text("SELECT to_regclass('auth.users') IS NOT NULL")):
        await db_session.execute(text("CREATE SCHEMA auth"))
        await db_session.execute(
            text(
                "CREATE TABLE auth.users (id uuid PRIMARY KEY, email text, "
                "created_at timestamptz, last_sign_in_at timestamptz)"
            )
        )
    me = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO auth.users (id, email, created_at) VALUES (:id, :email, now())"),
        {"id": me, "email": f"{me.hex}@example.invalid"},
    )
    await db_session.commit()

    async with api_client(db_session) as client:
        body = (await client.get("/me/export", headers=auth(me))).json()
    assert body["account"]["email"] == f"{me.hex}@example.invalid"
    assert body["account"]["last_sign_in_at"] is None
