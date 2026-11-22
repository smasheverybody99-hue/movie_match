"""The shape rules for client events (app/services/events.py), without a database."""

from datetime import UTC, datetime, timedelta

import pytest

from app.schemas import EventIn
from app.services import events
from app.services.events import ClientEvent, EventRejected, check

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


def test_the_client_types_are_a_subset_of_the_event_types() -> None:
    assert events.CLIENT_EVENT_TYPES < events.EVENT_TYPES
    # The prompt's eight, no more.
    assert events.EVENT_TYPES == {
        "recommendation_shown",
        "recommendation_clicked",
        "added_to_watchlist",
        "marked_watched",
        "rated",
        "assistant_query",
        "onboarding_step",
        "onboarding_done",
    }


def test_the_sources_are_the_home_sections_and_the_assistant() -> None:
    from typing import get_args

    from app.schemas import SectionKey

    assert set(get_args(SectionKey)) | {"assistant"} == events.SOURCES


@pytest.mark.parametrize(
    "event",
    [
        ClientEvent("recommendation_shown", NOW, movie_id=1, source="for_you"),
        ClientEvent("recommendation_clicked", NOW, movie_id=1, source="assistant"),
        ClientEvent("onboarding_step", NOW, props={"step": "rate"}),
        ClientEvent("recommendation_shown", NOW - timedelta(days=6, hours=23), 1, "under_90"),
        ClientEvent("recommendation_shown", NOW + timedelta(minutes=4), 1, "under_90"),
    ],
)
def test_well_formed_events_pass(event: ClientEvent) -> None:
    check(event, NOW)


@pytest.mark.parametrize(
    ("event", "why"),
    [
        (ClientEvent("rated", NOW, movie_id=1), "not an event the client sends"),
        (ClientEvent("assistant_query", NOW), "not an event the client sends"),
        (ClientEvent("made_up", NOW), "not an event the client sends"),
        (ClientEvent("recommendation_shown", NOW, source="for_you"), "needs a film"),
        (ClientEvent("recommendation_shown", NOW, movie_id=1), "needs a source"),
        (ClientEvent("recommendation_shown", NOW, movie_id=1, source="search"), "needs a source"),
        (
            ClientEvent("recommendation_shown", NOW, 1, "for_you", props={"step": "pick"}),
            "takes no props",
        ),
        (ClientEvent("onboarding_step", NOW), "needs props"),
        (ClientEvent("onboarding_step", NOW, props={"step": "later"}), "needs props"),
        (ClientEvent("onboarding_step", NOW, movie_id=1, props={"step": "pick"}), "no film"),
        (
            ClientEvent("recommendation_shown", NOW - timedelta(days=8), 1, "for_you"),
            "too far",
        ),
        (
            ClientEvent("recommendation_shown", NOW + timedelta(minutes=6), 1, "for_you"),
            "too far",
        ),
        (
            ClientEvent("recommendation_shown", NOW.replace(tzinfo=None), 1, "for_you"),
            "no time zone",
        ),
    ],
)
def test_malformed_events_are_rejected(event: ClientEvent, why: str) -> None:
    with pytest.raises(EventRejected, match=why):
        check(event, NOW)


def test_the_schema_refuses_fields_it_does_not_know() -> None:
    """Nothing but the five fields: a client cannot attach the text of a search box."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        EventIn.model_validate(
            {
                "type": "recommendation_shown",
                "at": NOW.isoformat(),
                "movie_id": 1,
                "source": "for_you",
                "query": "films like the one my ex liked",
            }
        )
