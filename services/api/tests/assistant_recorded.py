"""The assistant on recorded model responses, and the SSE stream read back as events.

`RecordedSdk` stands in for the Gemini async client: each `generate_content_stream` call
plays the next call of a fixture in tests/fixtures/assistant/ and keeps the request it was
given, so a test can check what the model would have been sent. The real GeminiAssistant
parses the chunks, so these tests cover the provider code as well as the service. No test
reaches a real model.

`"tool_call#2"` plays only the second call of a fixture. A chunk `{"raise": {"code": 503,
...}}` raises the SDK's own error at that point of the stream, as a 503 under load does;
`{"sleep": 2.0}` waits that many seconds there, as a slow or stalled stream does.
"""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from google.genai import errors, types

from app.providers.gemini import GeminiAssistant
from tests.conftest import load_fixture


class RecordedSdk:
    def __init__(self, *names: str) -> None:
        """The calls of each named fixture, in order; `names` may repeat."""
        self.calls: list[list[dict]] = []
        for name in names:
            fixture, _, which = name.partition("#")
            calls = load_fixture(f"assistant/{fixture}.json")["calls"]
            self.calls += [calls[int(which) - 1]] if which else calls
        self.requests: list[dict[str, Any]] = []

    @property
    def models(self) -> "RecordedSdk":
        return self

    async def generate_content_stream(
        self, *, model: str, contents: list[Any], config: dict[str, Any]
    ) -> AsyncIterator[types.GenerateContentResponse]:
        if len(self.requests) >= len(self.calls):
            raise AssertionError(f"model called {len(self.requests) + 1} times, recorded fewer")
        chunks = self.calls[len(self.requests)]
        self.requests.append({"model": model, "contents": contents, "config": config})

        async def play() -> AsyncIterator[types.GenerateContentResponse]:
            for chunk in chunks:
                if "sleep" in chunk:
                    await asyncio.sleep(chunk["sleep"])
                    continue
                if "raise" in chunk:
                    error = chunk["raise"]
                    kind = errors.ServerError if error["code"] >= 500 else errors.ClientError
                    raise kind(error["code"], {"error": error})
                yield types.GenerateContentResponse.model_validate(chunk)

        return play()


def recorded_assistant(*names: str) -> tuple[GeminiAssistant, RecordedSdk]:
    sdk = RecordedSdk(*names)
    return GeminiAssistant(sdk), sdk


def events(body: str) -> list[tuple[str, Any]]:
    """An SSE body -> [(event name, decoded data)], in order."""
    out = []
    for block in body.split("\n\n"):
        if not block.strip():
            continue
        name, data = "", ""
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line[len("event: ") :]
            elif line.startswith("data: "):
                data = line[len("data: ") :]
        out.append((name, json.loads(data)))
    return out


def text_of(stream: list[tuple[str, Any]]) -> str:
    return "".join(data["text"] for name, data in stream if name == "text")


def card_ids(stream: list[tuple[str, Any]]) -> list[int]:
    return [data["movie"]["id"] for name, data in stream if name == "card"]


def user_texts(request: dict[str, Any]) -> list[str]:
    """The text of every user message in a recorded request, oldest first."""
    return [
        part["text"]
        for content in request["contents"]
        if content["role"] == "user"
        for part in content["parts"]
        if isinstance(part, dict) and "text" in part
    ]
