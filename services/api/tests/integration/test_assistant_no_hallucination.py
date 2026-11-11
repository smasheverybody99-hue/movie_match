"""Every film in a rendered answer exists in the database and came from the engine.

The recorded answer names four ids: two the search returned, 424242 (in no database) and
a film the viewer has already rated (in the database, but never returned by a search). Only
the first two may become cards from the answer's markers."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AssistantTurn, Movie
from tests.assistant_recorded import card_ids, events, recorded_assistant, text_of
from tests.conftest import requires_db
from tests.integration.api import api_client, auth
from tests.integration.assistant_world import RATED, SHORT, UNKNOWN_ID, new_viewer

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]


async def test_an_unknown_or_unreturned_film_id_is_dropped(
    assistant_catalogue: AsyncSession,
) -> None:
    session = assistant_catalogue
    me = await new_viewer(session)
    assistant, _ = recorded_assistant("tool_call")
    async with api_client(session, assistant=assistant) as client:
        response = await client.post(
            "/assistant/chat", json={"message": "Something twisty"}, headers=auth(me)
        )
    assert response.status_code == 200, response.text
    stream = events(response.text)

    ids = card_ids(stream)
    assert UNKNOWN_ID not in ids
    assert RATED[0] not in ids
    assert set(ids) <= set(SHORT)
    in_db = set(await session.scalars(select(Movie.id).where(Movie.id.in_(ids))))
    assert in_db == set(ids)

    # No marker reaches the text, dropped or not.
    text = text_of(stream)
    assert "[[" not in text and "]]" not in text
    assert str(UNKNOWN_ID) not in text

    turn = await session.scalar(select(AssistantTurn).where(AssistantTurn.user_id == me))
    assert turn is not None
    assert turn.movie_ids == ids
