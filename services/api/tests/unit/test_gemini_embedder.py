"""GeminiEmbedder against a fake client. Responses are built with the SDK's own types."""

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from google.genai import errors, types
from tenacity import wait_none

from app.config import Settings
from app.models import EMBEDDING_DIM
from app.pipelines.embeddings import (
    EMBED_ATTEMPTS,
    EMBEDDING_MODEL,
    GeminiEmbedder,
    get_embedder,
)


def _response(values: list[float]) -> types.EmbedContentResponse:
    return types.EmbedContentResponse.model_validate({"embeddings": [{"values": values}]})


def _api_error(code: int) -> errors.APIError:
    cls = errors.ClientError if code < 500 else errors.ServerError
    return cls(code, {"error": {"code": code, "message": "nope", "status": "X"}})


class FakeModels:
    """`client.models`: the vector for a text is [len(text), 0, 0, ...], so order is checkable."""

    def __init__(self, *, failures: list[int] | None = None, bad: Any = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._failures = list(failures or [])
        self._bad = bad

    async def embed_content(self, *, model: str, contents: str, config: Any) -> Any:
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self._failures:
            raise _api_error(self._failures.pop(0))
        if self._bad is not None:
            return self._bad
        # Shorter texts answer later, so finishing order differs from request order.
        await asyncio.sleep(0.002 * max(0, 40 - len(contents)))
        return _response([float(len(contents))] + [0.0] * (EMBEDDING_DIM - 1))


def _embedder(models: FakeModels, **kwargs: Any) -> GeminiEmbedder:
    return GeminiEmbedder(SimpleNamespace(models=models), wait=wait_none(), **kwargs)


async def test_one_request_per_text_at_the_column_size() -> None:
    models = FakeModels()
    vectors = await _embedder(models).embed(["alpha", "beta", "gamma"])

    assert len(models.calls) == 3  # Embedding 2 aggregates a list into ONE vector
    assert all(len(v) == EMBEDDING_DIM for v in vectors)
    for call in models.calls:
        assert call["model"] == EMBEDDING_MODEL == "gemini-embedding-2"
        assert call["config"].output_dimensionality == EMBEDDING_DIM == 1536
        assert call["contents"].startswith("title: none | text: ")


async def test_vectors_come_back_in_the_order_of_the_texts() -> None:
    texts = ["x" * n for n in (30, 5, 20, 1, 12)]
    vectors = await _embedder(FakeModels(), concurrency=3).embed(texts)
    # each vector's first value is the length of the sent content: prefix + text
    prefix = len("title: none | text: ")
    assert [v[0] for v in vectors] == [float(prefix + len(t)) for t in texts]


async def test_no_texts_no_calls() -> None:
    models = FakeModels()
    assert await _embedder(models).embed([]) == []
    assert models.calls == []


async def test_a_rate_limit_is_retried() -> None:
    models = FakeModels(failures=[429, 503])
    vectors = await _embedder(models).embed(["alpha"])
    assert len(vectors) == 1
    assert len(models.calls) == 3


async def test_gives_up_after_the_attempt_limit() -> None:
    models = FakeModels(failures=[429] * (EMBED_ATTEMPTS + 3))
    with pytest.raises(ExceptionGroup) as raised:
        await _embedder(models).embed(["alpha"])
    assert isinstance(raised.value.exceptions[0], errors.APIError)
    assert len(models.calls) == EMBED_ATTEMPTS


async def test_a_bad_request_is_not_retried() -> None:
    models = FakeModels(failures=[400])
    with pytest.raises(ExceptionGroup) as raised:
        await _embedder(models).embed(["alpha"])
    assert raised.value.exceptions[0].code == 400  # type: ignore[attr-defined]
    assert len(models.calls) == 1


@pytest.mark.parametrize(
    "bad",
    [
        types.EmbedContentResponse(embeddings=[]),
        types.EmbedContentResponse(embeddings=None),
        types.EmbedContentResponse.model_validate(
            {"embeddings": [{"values": [1.0]}, {"values": [2.0]}]}
        ),
        types.EmbedContentResponse.model_validate({"embeddings": [{"values": []}]}),
    ],
    ids=["empty", "none", "aggregated-into-two", "no-values"],
)
async def test_a_response_that_is_not_one_vector_is_rejected(bad: Any) -> None:
    with pytest.raises(ExceptionGroup) as raised:
        await _embedder(FakeModels(bad=bad)).embed(["alpha"])
    assert isinstance(raised.value.exceptions[0], ValueError)


def test_embedder_reports_the_column_size() -> None:
    embedder = _embedder(FakeModels())
    assert (embedder.model, embedder.dim) == (EMBEDDING_MODEL, EMBEDDING_DIM)


def test_with_a_key_the_embedder_builds_without_touching_the_network() -> None:
    embedder = get_embedder(Settings(_env_file=None, gemini_api_key="test-key"))
    assert isinstance(embedder, GeminiEmbedder)
