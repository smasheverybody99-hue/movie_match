"""No event payload holds text the user typed (Phase 5).

Every way an event is made runs once - an assistant message, a search-like batch, a
rating, the watchlist, onboarding - with a phrase only the user could have typed, and
then every stored event of that user is read back column by column.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event
from app.services import events
from tests.assistant_recorded import recorded_assistant
from tests.conftest import requires_db
from tests.integration.api import api_client, auth
from tests.integration.assistant_world import RATED, new_viewer

TYPED = "my neighbour Dilnoza recommended this zxq-7731"


def _stored_text(event: Event) -> str:
    """Everything the row holds, as one string."""
    return " ".join(str(getattr(event, column.key)) for column in Event.__table__.columns)


@requires_db
@pytest.mark.asyncio(loop_scope="module")
async def test_no_event_holds_what_the_user_typed(assistant_catalogue: AsyncSession) -> None:
    session = assistant_catalogue
    me = await new_viewer(session)
    film = RATED[0]
    assistant, _ = recorded_assistant("plain_answer")
    now = datetime.now(UTC).isoformat()
    async with api_client(session, assistant=assistant) as client:
        chat = await client.post("/assistant/chat", json={"message": TYPED}, headers=auth(me))
        assert chat.status_code == 200
        await client.post("/ratings", json={"movie_id": film, "score": 7}, headers=auth(me))
        await client.post("/watchlist", json={"movie_id": film}, headers=auth(me))
        await client.post(f"/watchlist/{film}/watched", headers=auth(me))
        await client.post("/onboarding/done", headers=auth(me))
        shown = {"type": "recommendation_shown", "at": now, "movie_id": film, "source": "assistant"}
        await client.post("/events", json={"events": [shown]}, headers=auth(me))
        # A client that tries to attach the text is refused, and nothing is written.
        leaky = await client.post(
            "/events", json={"events": [{**shown, "query": TYPED}]}, headers=auth(me)
        )
        assert leaky.status_code == 422

    session.expire_all()
    stored = list((await session.scalars(select(Event).where(Event.user_id == me))).all())
    assert {e.type for e in stored} == {
        "assistant_query",
        "rated",
        "added_to_watchlist",
        "marked_watched",
        "onboarding_done",
        "recommendation_shown",
    }
    for event in stored:
        text = _stored_text(event)
        assert TYPED not in text
        assert "zxq-7731" not in text and "Dilnoza" not in text
        assert event.source is None or event.source in events.SOURCES
        # props: enumerated values only, never a string of the user's.
        assert all(key == "step" for key in event.props), event.props
        assert all(value in events.ONBOARDING_STEPS for value in event.props.values())


def test_the_events_table_has_no_column_for_free_text() -> None:
    """A new column has to come through this test, and through its reviewer."""
    assert {c.key for c in Event.__table__.columns} == {
        "id",
        "user_id",
        "type",
        "movie_id",
        "source",
        "props",
        "occurred_at",
        "received_at",
    }


def test_onboarding_props_carry_only_a_step() -> None:
    now = datetime.now(UTC)
    with pytest.raises(events.EventRejected):
        events.check(
            events.ClientEvent("onboarding_step", now, props={"step": "pick", "note": TYPED}), now
        )
    with pytest.raises(events.EventRejected):
        events.check(events.ClientEvent("onboarding_step", now, props={"step": TYPED}), now)
    events.check(events.ClientEvent("onboarding_step", now, props={"step": "done"}), now)
