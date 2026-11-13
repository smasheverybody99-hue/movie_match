"""A recorded model response asks for search_movies: the right arguments reach
recommend.search, and its films are what the model is shown and what the user gets."""

import logging

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import assistant as service
from app.services import recommend
from app.services.recommend import SearchRequest
from tests.assistant_recorded import card_ids, events, recorded_assistant
from tests.conftest import requires_db
from tests.integration.api import api_client, auth
from tests.integration.assistant_world import SHORT, new_viewer

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]

QUESTION = "I have 90 minutes, blow my mind"


@pytest.fixture
def spy(monkeypatch: pytest.MonkeyPatch) -> list[SearchRequest]:
    """Every request that reaches the engine; the engine itself still runs."""
    seen: list[SearchRequest] = []
    real = recommend.search

    async def search(session, user_id, request, now=None):  # type: ignore[no-untyped-def]
        seen.append(request)
        return await real(session, user_id, request, now)

    monkeypatch.setattr(recommend, "search", search)
    return seen


async def _ask(session: AsyncSession, spy: list[SearchRequest]):  # type: ignore[no-untyped-def]
    me = await new_viewer(session)
    assistant, sdk = recorded_assistant("tool_call")
    async with api_client(session, assistant=assistant) as client:
        response = await client.post(
            "/assistant/chat", json={"message": QUESTION}, headers=auth(me)
        )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/event-stream")
    return events(response.text), sdk


async def test_the_models_arguments_reach_the_engine(
    assistant_catalogue: AsyncSession, spy: list[SearchRequest]
) -> None:
    await _ask(assistant_catalogue, spy)

    assert len(spy) == 1
    request = spy[0]
    # Explicit traits win over the mood's own levels for the same keys.
    assert request.targets == {"psychological_complexity": 85.0, "plot_twist": 80.0}
    assert request.runtime_max == 90
    assert request.year_min == 1990
    assert request.year_max is None
    assert 9_600_006 in request.exclude


async def test_the_model_is_shown_the_engines_films_and_its_own_call_back(
    assistant_catalogue: AsyncSession, spy: list[SearchRequest]
) -> None:
    _, sdk = await _ask(assistant_catalogue, spy)

    assert len(sdk.requests) == 2  # the call that asks for the tool, the answer after it
    first, second = sdk.requests
    assert first["config"]["tool_config"]["function_calling_config"]["mode"] == "AUTO"
    assert second["config"]["tool_config"]["function_calling_config"]["mode"] == "NONE"

    model_turn, tool_turn = second["contents"][-2:]
    # The model's own part goes back unchanged, thought signature included (Gemini 3).
    assert model_turn["role"] == "model"
    assert model_turn["parts"][0].thought_signature == b"signature-1"
    response = tool_turn["parts"][0]["function_response"]
    assert response["name"] == "search_movies"
    ids = [film["id"] for film in response["response"]["films"]]
    assert ids and set(ids) <= set(SHORT[:5])
    film = response["response"]["films"][0]
    assert set(film) == {"id", "title", "year", "runtime_minutes", "genres", "overview"}
    assert film["runtime_minutes"] <= 90 and film["year"] >= 1990


async def test_only_the_films_the_answer_placed_are_shown_in_its_order(
    assistant_catalogue: AsyncSession, spy: list[SearchRequest]
) -> None:
    stream, _ = await _ask(assistant_catalogue, spy)

    # The engine found five; the answer placed two. The other three are not appended
    # (until 2026-11-13 they were, and the manual checks found them off the request).
    assert card_ids(stream) == [9_600_001, 9_600_002]
    followups = [data["items"] for name, data in stream if name == "followups"]
    assert followups == [["Something even shorter", "Older films like these"]]
    assert stream[-1] == ("done", {})
    card = next(data for name, data in stream if name == "card")
    assert set(card) == {"movie", "match", "band"}
    assert 0 <= card["match"] <= 100


# --- the opening sentence and genres (2026-11-13) --------------------------------------


async def test_the_intro_shows_before_the_search_and_the_genre_reaches_it(
    assistant_catalogue: AsyncSession,
    spy: list[SearchRequest],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.services.assistant")
    me = await new_viewer(assistant_catalogue)
    assistant, sdk = recorded_assistant("intro_tool_call", "tool_call#2")
    async with api_client(assistant_catalogue, assistant=assistant) as client:
        response = await client.post(
            "/assistant/chat", json={"message": "A short twisty thriller"}, headers=auth(me)
        )
    assert response.status_code == 200, response.text
    stream = events(response.text)

    # The model wrote no text in the first call: the first words are the call's intro.
    assert stream[0] == ("text", {"text": "Looking for short, twisty thrillers. "})
    assert stream[1] == (
        "text",
        {"text": "Two short ones that keep you guessing. This one turns on what its hero "},
    )
    assert [name for name, _ in stream].index("card") > 1
    assert spy[0].genres == frozenset({"Thriller"})  # "thriller" matched to TMDB's name
    assert set(card_ids(stream)) <= set(SHORT)
    # The model gets its own call back, intro included, so it need not repeat it.
    model_turn = sdk.requests[1]["contents"][-2]
    assert model_turn["role"] == "model"
    call = model_turn["parts"][0].function_call
    assert call.name == "search_movies"
    assert call.args["intro"] == "Looking for short, twisty thrillers."
    assert stream[-1] == ("done", {})
    line = next(r.getMessage() for r in caplog.records if "assistant timing" in r.getMessage())
    assert "first_call_text=0 " in line
    assert line.startswith("assistant timing jwt=")


async def test_a_film_must_have_every_genre_asked_for(
    assistant_catalogue: AsyncSession,
) -> None:
    me = await new_viewer(assistant_catalogue)

    thrillers = await service.search_movies(assistant_catalogue, me, genres=["Thriller"])
    assert thrillers.hits and {h.movie.id for h in thrillers.hits} <= set(SHORT)
    both = await service.search_movies(assistant_catalogue, me, genres=["Thriller", "Comedy"])
    assert both.hits == []
