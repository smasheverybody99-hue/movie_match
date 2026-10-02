"""Sync trait mode without a network or a database: retries, pacing and the Gemini scorer
over a fake SDK. The provider-neutral part never sees a vendor type."""

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from google.genai import errors, types

from app.config import Settings
from app.pipelines import traits
from app.pipelines.traits import MAX_BACKOFF_SECONDS, build_request, call_with_retries
from app.providers.base import ProviderUnavailable, RateLimited, TransientError
from app.providers.gemini import (
    TRAIT_MODEL,
    TRAIT_SYNC_PRICING,
    GeminiTraitScorer,
    trait_config,
)
from app.providers.gemini import (
    build_request as gemini_batch_request,
)

FILM = {"id": 550, "title": "Fight Club", "year": 1999}
VALID = '{"psychological_complexity": 85}'


class Sleeps:
    """Records waits instead of waiting."""

    def __init__(self) -> None:
        self.waits: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.waits.append(seconds)


def failing(*errors_then_value: Any):  # type: ignore[no-untyped-def]
    """A call that raises the given exceptions in turn, then returns the last item."""
    queue = list(errors_then_value)
    calls = {"n": 0}

    async def call() -> Any:
        calls["n"] += 1
        item = queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    return call, calls


# --- retries --------------------------------------------------------------------------


async def test_a_success_needs_no_wait() -> None:
    sleep = Sleeps()
    call, calls = failing("ok")
    assert await call_with_retries(call, retries=3, base_delay=6, sleep=sleep) == "ok"
    assert (calls["n"], sleep.waits) == (1, [])


async def test_a_rate_limit_waits_the_providers_hint() -> None:
    sleep = Sleeps()
    call, calls = failing(RateLimited("429", retry_after=37), "ok")
    assert await call_with_retries(call, retries=3, base_delay=6, sleep=sleep) == "ok"
    assert (calls["n"], sleep.waits) == (2, [37])


async def test_without_a_hint_the_wait_doubles_and_is_capped() -> None:
    sleep = Sleeps()
    call, _ = failing(*(TransientError("503") for _ in range(4)), RateLimited("429"), "ok")
    await call_with_retries(call, retries=5, base_delay=40, sleep=sleep)
    assert sleep.waits == [40, 80, MAX_BACKOFF_SECONDS, MAX_BACKOFF_SECONDS, MAX_BACKOFF_SECONDS]


async def test_after_the_last_retry_the_error_is_raised() -> None:
    sleep = Sleeps()
    call, calls = failing(*(RateLimited("429") for _ in range(3)))
    with pytest.raises(RateLimited):
        await call_with_retries(call, retries=2, base_delay=1, sleep=sleep)
    assert calls["n"] == 3


async def test_an_account_refusal_is_never_retried() -> None:
    sleep = Sleeps()
    call, calls = failing(ProviderUnavailable("400 FAILED_PRECONDITION"), "ok")
    with pytest.raises(ProviderUnavailable):
        await call_with_retries(call, retries=5, base_delay=1, sleep=sleep)
    assert (calls["n"], sleep.waits) == (1, [])


# --- the Gemini scorer over a fake SDK ------------------------------------------------


def _api_error(code: int, status: str, details: list | None = None) -> errors.APIError:
    cls = errors.ClientError if code < 500 else errors.ServerError
    body: dict[str, Any] = {"code": code, "message": "nope", "status": status}
    if details:
        body["details"] = details
    return cls(code, {"error": body})


def _response(text: str, finish: str = "STOP") -> types.GenerateContentResponse:
    return types.GenerateContentResponse.model_validate(
        {
            "candidates": [
                {"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": finish}
            ],
            "usageMetadata": {
                "promptTokenCount": 370,
                "candidatesTokenCount": 180,
                "thoughtsTokenCount": 15,
            },
        }
    )


class FakeModels:
    def __init__(self, outcome: Any) -> None:
        self.outcome = outcome
        self.calls: list[dict[str, Any]] = []

    async def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def _scorer(outcome: Any) -> tuple[GeminiTraitScorer, FakeModels]:
    models = FakeModels(outcome)
    return GeminiTraitScorer(Settings(_env_file=None), sdk=SimpleNamespace(models=models)), models


async def test_sync_sends_exactly_what_a_batch_request_carries() -> None:
    scorer, models = _scorer(_response(VALID))
    request = build_request(FILM)
    await scorer.score(request)
    (call,) = models.calls
    assert call["model"] == TRAIT_MODEL
    assert call["contents"] == request.prompt
    assert call["config"] == trait_config(request) == gemini_batch_request(request)["config"]


async def test_an_answer_comes_back_with_its_tokens() -> None:
    scorer, _ = _scorer(_response(VALID))
    answer = await scorer.score(build_request(FILM))
    assert (answer.key, answer.text, answer.error) == ("movie-550", VALID, None)
    assert (answer.usage.input_tokens, answer.usage.output_tokens) == (370, 195)
    assert scorer.pricing is TRAIT_SYNC_PRICING  # standard rate, not the batch one


async def test_a_truncated_answer_is_a_failed_film_not_text() -> None:
    scorer, _ = _scorer(_response('{"psy', finish="MAX_TOKENS"))
    answer = await scorer.score(build_request(FILM))
    assert (answer.text, answer.error) == (None, "truncated at max_tokens")


async def test_429_is_rate_limited_with_googles_retry_hint() -> None:
    hint = [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "37s"}]
    scorer, _ = _scorer(_api_error(429, "RESOURCE_EXHAUSTED", hint))
    with pytest.raises(RateLimited) as raised:
        await scorer.score(build_request(FILM))
    assert raised.value.retry_after == 37


async def test_a_server_error_is_transient() -> None:
    scorer, _ = _scorer(_api_error(503, "UNAVAILABLE"))
    with pytest.raises(TransientError):
        await scorer.score(build_request(FILM))


@pytest.mark.parametrize(
    ("code", "status"),
    [(400, "FAILED_PRECONDITION"), (403, "PERMISSION_DENIED"), (401, "UNAUTHENTICATED")],
)
async def test_an_account_problem_stops_the_run(code: int, status: str) -> None:
    scorer, _ = _scorer(_api_error(code, status))
    with pytest.raises(ProviderUnavailable, match=status):
        await scorer.score(build_request(FILM))


async def test_any_other_refusal_is_one_failed_film() -> None:
    scorer, _ = _scorer(_api_error(400, "INVALID_ARGUMENT"))
    answer = await scorer.score(build_request(FILM))
    assert answer.text is None
    assert answer.error is not None and answer.error.startswith("refused: 400 INVALID_ARGUMENT")


def test_without_a_key_nothing_is_sent() -> None:
    scorer = GeminiTraitScorer(Settings(_env_file=None))
    with pytest.raises(SystemExit, match="GEMINI_API_KEY"):
        scorer._client()


def test_batch_stays_the_default_mode() -> None:
    settings = Settings(_env_file=None)
    assert settings.trait_mode == "batch"
    assert settings.trait_sync_requests_per_minute == 10


def test_the_sync_estimate_uses_the_standard_rate() -> None:
    estimate = traits.estimate_cost([FILM], TRAIT_SYNC_PRICING)
    batch = traits.estimate_cost(
        [FILM], traits.get_provider(Settings(_env_file=None)).trait_extractor().pricing
    )
    assert estimate.usd == pytest.approx(batch.usd * 2)


def _blocked() -> types.GenerateContentResponse:
    return types.GenerateContentResponse.model_validate(
        {
            "promptFeedback": {"blockReason": "PROHIBITED_CONTENT"},
            "usageMetadata": {"promptTokenCount": 360},
        }
    )


async def test_a_blocked_prompt_is_a_final_answer() -> None:
    """The safety filter refuses the same prompt every time: no point asking again."""
    scorer, _ = _scorer(_blocked())
    answer = await scorer.score(build_request(FILM))
    assert answer.text is None and answer.final is True
    assert answer.error is not None and "PROHIBITED_CONTENT" in answer.error
    assert answer.usage.input_tokens == 360


async def test_other_failed_answers_are_not_final() -> None:
    for outcome in (_response('{"psy', finish="MAX_TOKENS"), _api_error(400, "INVALID_ARGUMENT")):
        scorer, _ = _scorer(outcome)
        assert (await scorer.score(build_request(FILM))).final is False


def test_a_blocked_batch_item_is_final_too() -> None:
    from app.providers.gemini import read_answer

    blocked = types.InlinedResponse.model_validate(
        {
            "metadata": {"key": "movie-1"},
            "response": {"promptFeedback": {"blockReason": "PROHIBITED_CONTENT"}},
        }
    )
    errored = types.InlinedResponse.model_validate(
        {"metadata": {"key": "movie-2"}, "error": {"code": 500, "message": "overloaded"}}
    )
    assert read_answer(blocked).final is True
    assert read_answer(errored).final is False


# --- network-level failures --------------------------------------------------------------


async def test_a_network_failure_is_transient_and_the_retry_succeeds() -> None:
    """The scorer turns a dropped connection into TransientError; call_with_retries then
    sends the same request again and the film is scored."""
    request_ = httpx.Request("POST", "https://generativelanguage.googleapis.com/")

    class DropsOnce(FakeModels):
        def __init__(self) -> None:
            super().__init__(_response(VALID))
            self.dropped = False

        async def generate_content(self, **kwargs: Any) -> Any:
            self.calls.append(kwargs)
            if not self.dropped:
                self.dropped = True
                raise httpx.RemoteProtocolError("Server disconnected", request=request_)
            return self.outcome

    models = DropsOnce()
    scorer = GeminiTraitScorer(Settings(_env_file=None), sdk=SimpleNamespace(models=models))
    sleep = Sleeps()
    answer = await call_with_retries(
        lambda: scorer.score(build_request(FILM)), retries=2, base_delay=6, sleep=sleep
    )
    assert answer.text == VALID
    assert len(models.calls) == 2 and sleep.waits == [6]
