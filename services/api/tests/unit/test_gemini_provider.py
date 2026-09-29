"""The Gemini implementation's wire format. No network: the SDK's own types check shapes."""

from google.genai import types

from app.pipelines.traits import RESPONSE_SCHEMA, SYSTEM_PROMPT, build_prompt
from app.pipelines.traits import build_request as neutral_request
from app.providers.gemini import (
    THINKING_LEVEL,
    TRAIT_MAX_OUTPUT_TOKENS,
    TRAIT_MODEL,
    build_request,
)

FILM = {"id": 550, "title": "Fight Club", "year": 1999}


def test_batch_request_shape() -> None:
    request = build_request(neutral_request(FILM))
    assert TRAIT_MODEL == "gemini-3.5-flash-lite"
    assert request["metadata"] == {"key": "movie-550"}
    assert request["contents"] == [{"role": "user", "parts": [{"text": build_prompt(FILM)}]}]
    config = request["config"]
    assert config["system_instruction"] == SYSTEM_PROMPT
    assert config["response_mime_type"] == "application/json"
    assert config["response_json_schema"] == RESPONSE_SCHEMA
    assert config["max_output_tokens"] == TRAIT_MAX_OUTPUT_TOKENS
    assert config["thinking_config"] == {"thinking_level": THINKING_LEVEL}
    assert "temperature" not in config  # Gemini 3 is tuned for its default


def test_batch_request_is_accepted_by_the_sdk_types() -> None:
    """The SDK models forbid unknown fields, so a misspelt key fails here, not in a paid run."""
    parsed = types.InlinedRequest.model_validate(build_request(neutral_request(FILM)))
    assert parsed.config is not None
    assert parsed.config.thinking_config is not None
    assert parsed.config.thinking_config.thinking_level == types.ThinkingLevel.MINIMAL
    assert parsed.metadata == {"key": "movie-550"}
