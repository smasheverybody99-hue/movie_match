"""GeminiEmbedder against a fake client. Responses are built with the SDK's own types.

One request per text, in order; no retries of its own (the pipeline paces and retries);
Gemini errors come out as the provider-neutral ones; tokens come from count_tokens.
"""

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from google.genai import errors, types

from app.config import Settings
from app.models import EMBEDDING_DIM
from app.pipelines.embeddings import get_embedder
from app.providers.base import (
    ProviderUnavailable,
    RateLimited,
    TransientError,
    UnsupportedDimension,
)
from app.providers.gemini import CHARS_PER_TOKEN, EMBEDDING_MODEL, GeminiEmbedder

NO_KEY = Settings(_env_file=None)


def _response(values: list[float]) -> types.EmbedContentResponse:
    return types.EmbedContentResponse.model_validate({"embeddings": [{"values": values}]})


def _api_error(code: int, status: str = "X", details: list | None = None) -> errors.APIError:
    cls = errors.ClientError if code < 500 else errors.ServerError
    body: dict[str, Any] = {"code": code, "message": "nope", "status": status}
    if details:
        body["details"] = details
    return cls(code, {"error": body})


class FakeModels:
    """`client.models`. The vector for a text is [len(content), 0, ...], so order shows;
    count_tokens answers len(content) // 4 unless told to fail."""

    def __init__(
        self, *, failure: Exception | None = None, bad: Any = None, count_fails: bool = False
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self.counted: list[str] = []
        self._failure = failure
        self._bad = bad
        self._count_fails = count_fails

    async def embed_content(self, *, model: str, contents: str, config: Any) -> Any:
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self._failure is not None:
            raise self._failure
        if self._bad is not None:
            return self._bad
        return _response([float(len(contents))] + [0.0] * (EMBEDDING_DIM - 1))

    async def count_tokens(self, *, model: str, contents: str) -> Any:
        self.counted.append(contents)
        if self._count_fails:
            raise _api_error(500, "INTERNAL")
        return SimpleNamespace(total_tokens=len(contents) // 4)


def _embedder(models: FakeModels) -> GeminiEmbedder:
    return GeminiEmbedder(NO_KEY, EMBEDDING_DIM, sdk=SimpleNamespace(models=models))


async def test_one_request_per_text_in_order_at_the_column_size() -> None:
    models = FakeModels()
    texts = ["x" * n for n in (30, 5, 20)]
    embedded = await _embedder(models).embed(texts)

    assert len(models.calls) == 3  # Embedding 2 aggregates a list into ONE vector
    prefix = len("title: none | text: ")
    assert [v[0] for v in embedded.vectors] == [float(prefix + len(t)) for t in texts]
    assert all(len(v) == EMBEDDING_DIM for v in embedded.vectors)
    for call in models.calls:
        assert call["model"] == EMBEDDING_MODEL == "gemini-embedding-2"
        assert call["config"].output_dimensionality == EMBEDDING_DIM == 1536
        assert call["contents"].startswith("title: none | text: ")


async def test_tokens_are_counted_by_the_provider_and_reported() -> None:
    models = FakeModels()
    embedded = await _embedder(models).embed(["alpha", "beta"])
    contents = [f"title: none | text: {t}" for t in ("alpha", "beta")]
    assert models.counted == contents  # counted exactly what was embedded
    assert embedded.usage.requests == 2
    assert embedded.usage.input_tokens == sum(len(c) // 4 for c in contents)
    assert embedded.usage.estimated is False


async def test_if_counting_fails_the_count_is_estimated_and_says_so() -> None:
    embedded = await _embedder(FakeModels(count_fails=True)).embed(["x" * 330])
    content = "title: none | text: " + "x" * 330
    assert embedded.usage.input_tokens == round(len(content) / CHARS_PER_TOKEN)
    assert embedded.usage.estimated is True
    assert len(embedded.vectors) == 1  # the embedding itself is not lost


async def test_no_texts_no_calls() -> None:
    models = FakeModels()
    assert (await _embedder(models).embed([])).vectors == []
    assert models.calls == [] and models.counted == []


async def test_a_rate_limit_is_rate_limited_with_the_hint_and_not_retried_here() -> None:
    hint = [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "12s"}]
    models = FakeModels(failure=_api_error(429, "RESOURCE_EXHAUSTED", hint))
    with pytest.raises(RateLimited) as raised:
        await _embedder(models).embed(["alpha"])
    assert raised.value.retry_after == 12
    assert len(models.calls) == 1  # the pipeline decides when to try again


async def test_a_server_error_is_transient() -> None:
    with pytest.raises(TransientError):
        await _embedder(FakeModels(failure=_api_error(503, "UNAVAILABLE"))).embed(["alpha"])


async def test_an_account_problem_is_provider_unavailable() -> None:
    models = FakeModels(failure=_api_error(400, "FAILED_PRECONDITION"))
    with pytest.raises(ProviderUnavailable, match="FAILED_PRECONDITION"):
        await _embedder(models).embed(["alpha"])


async def test_any_other_refusal_is_raised_as_it_came() -> None:
    models = FakeModels(failure=_api_error(400, "INVALID_ARGUMENT"))
    with pytest.raises(errors.ClientError):
        await _embedder(models).embed(["alpha"])


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
    with pytest.raises(ValueError, match="expected one embedding"):
        await _embedder(FakeModels(bad=bad)).embed(["alpha"])


def test_embedder_reports_the_column_size() -> None:
    embedder = _embedder(FakeModels())
    assert (embedder.model, embedder.dim) == (EMBEDDING_MODEL, EMBEDDING_DIM)


def test_the_configured_embedder_builds_without_a_key_or_the_network() -> None:
    embedder = get_embedder(NO_KEY)
    assert isinstance(embedder, GeminiEmbedder)
    assert embedder.dim == NO_KEY.embedding_dim == 1536


def test_the_embedder_is_built_at_the_configured_size() -> None:
    assert get_embedder(Settings(_env_file=None, embedding_dim=1024)).dim == 1024


@pytest.mark.parametrize("dim", [0, 3073])
def test_a_size_the_model_cannot_produce_is_refused(dim: int) -> None:
    with pytest.raises(UnsupportedDimension, match=str(dim)):
        GeminiEmbedder(NO_KEY, dim)


async def test_without_a_key_the_first_real_call_says_so() -> None:
    with pytest.raises(SystemExit, match="GEMINI_API_KEY"):
        await GeminiEmbedder(NO_KEY, EMBEDDING_DIM).embed(["alpha"])


# --- network-level failures (2026-10-01: the server hung up mid-run) ---------------------

_REQUEST = httpx.Request("POST", "https://generativelanguage.googleapis.com/")


@pytest.mark.parametrize(
    "failure",
    [
        httpx.RemoteProtocolError(
            "Server disconnected without sending a response.", request=_REQUEST
        ),
        httpx.ConnectError("connection refused", request=_REQUEST),
        httpx.ReadTimeout("read timed out", request=_REQUEST),
        ConnectionResetError("connection reset by peer"),
    ],
    ids=["server-hung-up", "connect", "read-timeout", "reset"],
)
async def test_a_network_failure_is_transient_so_the_pipeline_retries(failure: Exception) -> None:
    with pytest.raises(TransientError, match="network"):
        await _embedder(FakeModels(failure=failure)).embed(["alpha"])


async def test_a_network_failure_while_counting_falls_back_to_the_estimate() -> None:
    class CountDrops(FakeModels):
        async def count_tokens(self, *, model: str, contents: str) -> Any:
            raise httpx.RemoteProtocolError("Server disconnected", request=_REQUEST)

    embedded = await _embedder(CountDrops()).embed(["alpha"])
    assert len(embedded.vectors) == 1  # the run goes on
    assert embedded.usage.estimated is True
