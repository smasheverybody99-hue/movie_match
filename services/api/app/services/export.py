"""A user's own data, as one JSON document (docs/legal.md §3: export must actually work).

Every table that references users.id is exported, found from the schema itself, so a
table added later is in the export without editing this file. Plus the Supabase sign-in
record (email, created, last sign-in) where the database has one, and the titles of the
films the rows mention, so the file reads without the catalogue.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Table, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base, Movie

FORMAT = "movie-match-export/1"


@dataclass(frozen=True)
class Export:
    format: str
    exported_at: datetime
    user_id: uuid.UUID
    account: dict[str, Any] | None
    tables: dict[str, list[dict[str, Any]]]
    movies: dict[str, str]


def user_tables() -> list[tuple[Table, str]]:
    """`users` itself (by id), then every table with a foreign key to users.id, by name."""
    users = Base.metadata.tables["users"]
    found: list[tuple[Table, str]] = []
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_keys:
            if fk.column.table is users and fk.column.name == "id":
                found.append((table, fk.parent.name))
                break
    return [(users, "id"), *sorted(found, key=lambda pair: pair[0].name)]


def _plain(value: Any) -> Any:
    """A value JSON can hold. Vectors (numpy arrays from pgvector) become lists."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "tolist"):
        return [float(v) for v in value.tolist()]
    return value


async def _account(session: AsyncSession, user_id: uuid.UUID) -> dict[str, Any] | None:
    """The sign-in record Supabase holds, when this database is a Supabase one."""
    if not await session.scalar(text("SELECT to_regclass('auth.users') IS NOT NULL")):
        return None
    row = (
        await session.execute(
            text("SELECT email, created_at, last_sign_in_at FROM auth.users WHERE id = :id"),
            {"id": user_id},
        )
    ).first()
    if row is None:
        return None
    return {key: _plain(value) for key, value in row._mapping.items()}


async def export_user(
    session: AsyncSession, user_id: uuid.UUID, now: datetime | None = None
) -> Export:
    tables: dict[str, list[dict[str, Any]]] = {}
    movie_ids: set[int] = set()
    for table, column in user_tables():
        query = select(table).where(table.c[column] == user_id).order_by(*table.primary_key.columns)
        rows = [dict(row._mapping) for row in (await session.execute(query)).all()]
        for row in rows:
            if isinstance(row.get("movie_id"), int):
                movie_ids.add(row["movie_id"])
            for listed in row.get("movie_ids") or []:
                if isinstance(listed, int):
                    movie_ids.add(listed)
        tables[table.name] = [{k: _plain(v) for k, v in row.items()} for row in rows]

    titles: dict[str, str] = {}
    if movie_ids:
        found = await session.execute(
            select(Movie.id, Movie.title).where(Movie.id.in_(movie_ids)).order_by(Movie.id)
        )
        titles = {str(movie_id): title for movie_id, title in found.all()}

    return Export(
        format=FORMAT,
        exported_at=now or datetime.now(UTC),
        user_id=user_id,
        account=await _account(session, user_id),
        tables=tables,
        movies=titles,
    )
