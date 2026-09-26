"""The trait prompt names every dimension and carries the film's actual data."""

from google.genai import types

from app.pipelines.traits import (
    MAX_OUTPUT_TOKENS,
    MODEL,
    RESPONSE_SCHEMA,
    SYSTEM_PROMPT,
    THINKING_LEVEL,
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
    assert MODEL == "gemini-3.5-flash-lite"
    assert request["metadata"] == {"key": "movie-550"}
    assert request["contents"] == [{"role": "user", "parts": [{"text": build_prompt(FILM)}]}]
    config = request["config"]
    assert config["system_instruction"] == SYSTEM_PROMPT
    assert config["response_mime_type"] == "application/json"
    assert config["response_json_schema"] == RESPONSE_SCHEMA
    assert config["max_output_tokens"] == MAX_OUTPUT_TOKENS
    assert config["thinking_config"] == {"thinking_level": THINKING_LEVEL}
    assert "temperature" not in config  # Gemini 3 is tuned for its default


def test_batch_request_is_accepted_by_the_sdk_types() -> None:
    """The SDK models forbid unknown fields, so a misspelt key fails here, not in a paid run."""
    parsed = types.InlinedRequest.model_validate(build_request(FILM))
    assert parsed.config is not None
    assert parsed.config.thinking_config is not None
    assert parsed.config.thinking_config.thinking_level == types.ThinkingLevel.MINIMAL
    assert parsed.metadata == {"key": "movie-550"}


def test_response_schema_asks_for_every_trait_in_vector_order() -> None:
    props = RESPONSE_SCHEMA["properties"]
    assert list(props)[: len(TRAIT_KEYS)] == list(TRAIT_KEYS)
    assert RESPONSE_SCHEMA["required"] == [*TRAIT_KEYS, "summary"]
    for key in TRAIT_KEYS:
        assert props[key] == {"type": "integer", "minimum": 0, "maximum": 100}


def test_custom_id_round_trip() -> None:
    assert movie_id_from(custom_id(27205)) == 27205


def test_foreign_custom_id_is_rejected() -> None:
    import pytest

    with pytest.raises(ValueError):
        movie_id_from("film-12")
    with pytest.raises(ValueError):
        movie_id_from("movie-abc")
