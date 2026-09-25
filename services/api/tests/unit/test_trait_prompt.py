"""The trait prompt names every dimension and carries the film's actual data."""

from app.pipelines.traits import (
    MAX_TOKENS,
    MODEL,
    SYSTEM_PROMPT,
    build_prompt,
    build_request,
    custom_id,
    movie_id_from,
)
from app.traits import TRAIT_KEYS

FILM = {
    "id": 550,
    "title": "Fight Club",
    "year": 1999,
    "runtime_minutes": 139,
    "genres": ["Drama", "Thriller"],
    "keywords": ["dual identity", "nihilism"],
    "director": "David Fincher",
    "overview": "A ticking-time-bomb insomniac and a slippery soap salesman...",
}


def test_system_prompt_names_every_trait_key() -> None:
    for key in TRAIT_KEYS:
        assert key in SYSTEM_PROMPT, key


def test_system_prompt_lists_keys_in_vector_order() -> None:
    positions = [SYSTEM_PROMPT.index(key) for key in TRAIT_KEYS]
    assert positions == sorted(positions)


def test_prompt_contains_the_films_data() -> None:
    prompt = build_prompt(FILM)
    assert "Title: Fight Club" in prompt
    assert "Year: 1999" in prompt
    assert "Runtime: 139 minutes" in prompt
    assert "Genres: Drama, Thriller" in prompt
    assert "Keywords: dual identity, nihilism" in prompt
    assert "Director: David Fincher" in prompt
    assert "Overview: A ticking-time-bomb insomniac" in prompt


def test_missing_data_is_marked_not_invented() -> None:
    prompt = build_prompt({"title": "Untitled"})
    assert "Year: unknown" in prompt
    assert "Runtime: unknown minutes" in prompt
    assert "Genres: unknown" in prompt
    assert "Keywords: none" in prompt
    assert "Director: unknown" in prompt
    assert "Overview: none" in prompt


def test_batch_request_shape() -> None:
    request = build_request(FILM)
    assert request["custom_id"] == "movie-550"
    params = request["params"]
    assert params["model"] == MODEL == "claude-haiku-4-5"
    assert params["max_tokens"] == MAX_TOKENS
    assert params["system"] == SYSTEM_PROMPT
    assert params["messages"] == [{"role": "user", "content": build_prompt(FILM)}]
    assert "temperature" not in params  # removed from the 1.x SDK surface


def test_custom_id_round_trip() -> None:
    assert movie_id_from(custom_id(27205)) == 27205


def test_foreign_custom_id_is_rejected() -> None:
    import pytest

    with pytest.raises(ValueError):
        movie_id_from("film-12")
    with pytest.raises(ValueError):
        movie_id_from("movie-abc")
