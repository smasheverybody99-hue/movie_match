""" "This recommendation was wrong" (Phase 5): data for the alpha, not support.

One row per user and film: pressing it again replaces the source and the reason. It
does not change what is recommended - no ranking change while the alpha runs (TZ 1.31);
the client only takes the card out of the view it is on (user decision, 2026-11-17).
"""

import uuid
from typing import Literal, get_args

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie, RecommendationFeedback
from app.services.events import Source
from app.services.ratings import MovieNotFound

# The client's chips, in its order: "I've seen it", "Not my genre", "Too old", "Other".
Reason = Literal["seen", "not_my_genre", "too_old", "other"]
REASONS: frozenset[str] = frozenset(get_args(Reason))


async def mark_wrong(
    session: AsyncSession,
    user_id: uuid.UUID,
    movie_id: int,
    source: Source,
    reason: Reason | None,
) -> None:
    if await session.get(Movie, movie_id) is None:
        raise MovieNotFound(movie_id)
    stmt = insert(RecommendationFeedback).values(
        user_id=user_id, movie_id=movie_id, source=source, reason=reason
    )
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=["user_id", "movie_id"],
            set_={
                "source": stmt.excluded.source,
                "reason": stmt.excluded.reason,
                "updated_at": func.now(),
            },
        )
    )
    await session.commit()
