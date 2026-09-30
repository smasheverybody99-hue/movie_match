"""Gemini: the current implementation of the three provider protocols (ADR 0004).

Everything Gemini-specific lives here: the SDK, request shapes, job states, the
`title: none | text:` embedding format, thinking settings, and the prices. Whether Gemini
stays the provider is open (ADR 0006).

The SDK client is built on the first network call, not in the constructor, so prices and
dry runs work without GEMINI_API_KEY.
"""

import asyncio
from collections.abc import Sequence
from typing import Any

from google import genai
from google.genai import errors, types
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import Settings
from app.providers.base import (
    Embedded,
    Explainer,
    Generated,
    JobState,
    Pricing,
    ProviderUnavailable,
    RateLimited,
    TraitAnswer,
    TraitBatchResult,
    TraitRequest,
    TransientError,
    UnsupportedDimension,
    Usage,
)

NAME = "gemini"

TRAIT_MODEL = "gemini-3.5-flash-lite"
EXPLAIN_MODEL = "gemini-3.5-flash-lite"
EMBEDDING_MODEL = "gemini-embedding-2"

_PRICES = "https://ai.google.dev/gemini-api/docs/pricing, paid tier, checked 2026-09-26"
# Batch API: half of the $0.30 / $2.50 standard rate.
TRAIT_PRICING = Pricing(0.15, 1.25, f"{TRAIT_MODEL} batch; {_PRICES}")
# One film at a time on the standard API (TRAIT_MODE=sync): the full rate. On the free
# tier these calls cost nothing, but the free tier is not what the price says (ADR 0006).
TRAIT_SYNC_PRICING = Pricing(0.30, 2.50, f"{TRAIT_MODEL} standard; {_PRICES}")
EXPLAIN_PRICING = Pricing(0.30, 2.50, f"{EXPLAIN_MODEL} standard; {_PRICES}")
# Embeddings bill input only. Standard rate: the Batch API would halve ~$0.09 per 5,000
# films, not worth a second polling loop (ADR 0004).
EMBEDDING_PRICING = Pricing(0.20, 0.0, f"{EMBEDDING_MODEL} standard; {_PRICES}")

# Expected trait output is ~250 tokens. The ceiling only guards truncation, and it also has
# to cover any thinking tokens, which Gemini counts against it and bills as output.
TRAIT_MAX_OUTPUT_TOKENS = 2048
EXPLAIN_MAX_OUTPUT_TOKENS = 512  # two sentences need ~80; the rest covers thinking
THINKING_LEVEL = "MINIMAL"  # scoring or explaining from given facts needs no reasoning

# Embedding 2 returns 3,072 dimensions by default and accepts any output_dimensionality
# up to that; the API normalises truncated vectors.
EMBEDDING_MAX_DIM = 3072
EMBED_CONCURRENCY = 8
EMBED_ATTEMPTS = 5
CHARS_PER_TOKEN = 3.5  # the embeddings API reports no token count
_BACKOFF = wait_exponential(multiplier=1, max=30)
_TRANSIENT_CODES = {429, 500, 502, 503, 504}


def client(settings: Settings) -> Any:
    """Async Gemini client (`client.batches`, `client.models`) or exit with a clear message."""
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY is not configured")
    return genai.Client(api_key=settings.gemini_api_key).aio


def _usage(metadata: Any) -> Usage:
    if metadata is None:
        return Usage(requests=1)
    return Usage(
        requests=1,
        input_tokens=metadata.prompt_token_count or 0,
        output_tokens=(metadata.candidates_token_count or 0) + (metadata.thoughts_token_count or 0),
    )


# --- traits -------------------------------------------------------------------------


def trait_config(request: TraitRequest) -> dict[str, Any]:
    """The generation config for one film; batch and sync send exactly the same."""
    return {
        "system_instruction": request.system,
        "response_mime_type": "application/json",
        "response_json_schema": request.schema,
        "max_output_tokens": TRAIT_MAX_OUTPUT_TOKENS,
        "thinking_config": {"thinking_level": THINKING_LEVEL},
    }


def build_request(request: TraitRequest) -> dict[str, Any]:
    """One film -> one inline batch request (a `types.InlinedRequest`).

    `metadata` is echoed back on the result; it is how a result finds its film.
    """
    return {
        "metadata": {"key": request.key},
        "contents": [{"role": "user", "parts": [{"text": request.prompt}]}],
        "config": trait_config(request),
    }


_STATES: dict[types.JobState, JobState] = {
    types.JobState.JOB_STATE_SUCCEEDED: "done",
    types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED: "done",
    types.JobState.JOB_STATE_FAILED: "failed",
    types.JobState.JOB_STATE_CANCELLED: "cancelled",
    types.JobState.JOB_STATE_EXPIRED: "expired",
}
_CLEAN_STOPS = (None, types.FinishReason.STOP, types.FinishReason.FINISH_REASON_UNSPECIFIED)


def read_item(item: types.InlinedResponse) -> tuple[str | None, str | None]:
    """One batch result -> (text to parse, None) or (None, why there is nothing to parse)."""
    if item.error is not None:
        return None, f"batch result errored: {item.error.message or item.error.code}"
    return read_candidates(item.response)


def read_candidates(response: Any) -> tuple[str | None, str | None]:
    """A generated response (batch item or sync call) -> (text, None) or (None, why not)."""
    candidates = (response.candidates if response else None) or []
    if not candidates:
        feedback = response.prompt_feedback if response else None
        blocked = feedback.block_reason if feedback and feedback.block_reason else None
        return None, f"no candidates (prompt blocked: {blocked})" if blocked else "no candidates"
    candidate = candidates[0]
    reason = candidate.finish_reason
    if reason == types.FinishReason.MAX_TOKENS:
        return None, "truncated at max_tokens"
    if reason not in _CLEAN_STOPS:
        return None, f"finish_reason {reason.value}"
    parts = (candidate.content.parts if candidate.content else None) or []
    return "".join(p.text for p in parts if p.text and not p.thought), None


def read_answer(item: types.InlinedResponse) -> TraitAnswer:
    text, error = read_item(item)
    usage = _usage(item.response.usage_metadata if item.response else None)
    return TraitAnswer(
        key=(item.metadata or {}).get("key", ""), text=text, error=error, usage=usage
    )


class GeminiTraitExtractor:
    """Trait scoring through the Gemini Batch API (half price, results within 24 hours)."""

    provider = NAME
    model = TRAIT_MODEL
    pricing = TRAIT_PRICING

    def __init__(self, settings: Settings, sdk: Any = None) -> None:
        self._settings = settings
        self._sdk = sdk  # tests pass a fake with `.batches`

    def _client(self) -> Any:
        if self._sdk is None:
            self._sdk = client(self._settings)
        return self._sdk

    async def submit(self, requests: Sequence[TraitRequest]) -> str:
        job = await self._client().batches.create(
            model=self.model,
            src=[build_request(r) for r in requests],
            config={"display_name": f"traits-{len(requests)}-films"},
        )
        return str(job.name)

    async def collect(self, job_id: str) -> TraitBatchResult:
        job = await self._client().batches.get(name=job_id)
        detail = job.state.value if job.state else "unknown"
        state = _STATES.get(job.state, "running") if job.state else "running"
        if state != "done":
            return TraitBatchResult(state=state, detail=detail)
        if job.dest is None or job.dest.inlined_responses is None:
            raise ValueError(f"batch {job_id} finished without inline results")
        return TraitBatchResult(
            state="done",
            detail=detail,
            answers=[read_answer(item) for item in job.dest.inlined_responses],
        )


def retry_after(error: errors.APIError) -> float | None:
    """Gemini's RetryInfo hint ("retryDelay": "37s") from a 429, in seconds, if present."""
    details = error.details if isinstance(error.details, dict) else {}
    for item in (details.get("error") or {}).get("details") or []:
        delay = item.get("retryDelay") if isinstance(item, dict) else None
        if isinstance(delay, str) and delay.endswith("s"):
            try:
                return float(delay[:-1])
            except ValueError:
                return None
    return None


# Errors that say "this account cannot do this", not "this film failed".
_ACCOUNT_STATUSES = {"FAILED_PRECONDITION", "PERMISSION_DENIED", "UNAUTHENTICATED"}


def read_response(key: str, response: Any) -> TraitAnswer:
    """A generate_content response -> the same answer shape as a batch item."""
    text, error = read_candidates(response)
    usage = _usage(getattr(response, "usage_metadata", None))
    return TraitAnswer(key=key, text=text, error=error, usage=usage)


class GeminiTraitScorer:
    """Trait scoring one film per request on the standard API (TRAIT_MODE=sync)."""

    provider = NAME
    model = TRAIT_MODEL
    pricing = TRAIT_SYNC_PRICING

    def __init__(self, settings: Settings, sdk: Any = None) -> None:
        self._settings = settings
        self._sdk = sdk  # tests pass a fake with `.models`

    def _client(self) -> Any:
        if self._sdk is None:
            self._sdk = client(self._settings)
        return self._sdk

    async def score(self, request: TraitRequest) -> TraitAnswer:
        try:
            response = await self._client().models.generate_content(
                model=self.model, contents=request.prompt, config=trait_config(request)
            )
        except errors.APIError as exc:
            message = f"{exc.code} {exc.status}: {exc.message}"
            if exc.code == 429:
                raise RateLimited(message, retry_after(exc)) from exc
            if exc.code is not None and exc.code >= 500:
                raise TransientError(message) from exc
            if exc.status in _ACCOUNT_STATUSES or exc.code in (401, 403):
                raise ProviderUnavailable(message) from exc
            return TraitAnswer(key=request.key, text=None, error=f"refused: {message}")
        except TimeoutError as exc:
            raise TransientError(f"timed out: {exc}") from exc
        return read_response(request.key, response)


# --- embeddings ----------------------------------------------------------------------


def _is_transient(exc: BaseException) -> bool:
    return isinstance(exc, errors.APIError) and exc.code in _TRANSIENT_CODES


class GeminiEmbedder:
    """Film text -> `dim`-d vectors through Gemini Embedding 2.

    The model returns ONE aggregated embedding for a request with several inputs, so each
    text is its own request. Requests run a few at a time; rate limits and server errors
    are retried with backoff, anything else stops the run.
    """

    provider = NAME
    model = EMBEDDING_MODEL
    pricing = EMBEDDING_PRICING

    def __init__(
        self,
        settings: Settings,
        dim: int,
        *,
        sdk: Any = None,
        concurrency: int = EMBED_CONCURRENCY,
        wait: Any = _BACKOFF,
    ) -> None:
        if not 1 <= dim <= EMBEDDING_MAX_DIM:
            raise UnsupportedDimension(
                f"{EMBEDDING_MODEL} produces 1..{EMBEDDING_MAX_DIM} dimensions, not {dim}"
            )
        self.dim = dim
        self._settings = settings
        self._sdk = sdk
        self._concurrency = concurrency
        self._wait = wait

    def _client(self) -> Any:
        if self._sdk is None:
            self._sdk = client(self._settings)
        return self._sdk

    async def embed(self, texts: Sequence[str]) -> Embedded:
        if texts:
            self._client()  # no key: stop here, before any task starts
        gate = asyncio.Semaphore(self._concurrency)

        async def one(text: str) -> list[float]:
            async with gate:
                return await self._embed_one(text)

        async with asyncio.TaskGroup() as group:  # a failure cancels the rest
            tasks = [group.create_task(one(t)) for t in texts]
        contents = [self._content(t) for t in texts]
        usage = Usage(
            requests=len(texts),
            input_tokens=round(sum(len(c) for c in contents) / CHARS_PER_TOKEN),
            estimated=True,
        )
        return Embedded(vectors=[t.result() for t in tasks], usage=usage)

    @staticmethod
    def _content(text: str) -> str:
        # Embedding 2 takes no task_type; the documented document format is "title | text".
        return f"title: none | text: {text}"

    async def _embed_one(self, text: str) -> list[float]:
        config = types.EmbedContentConfig(output_dimensionality=self.dim)
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(_is_transient),
            wait=self._wait,
            stop=stop_after_attempt(EMBED_ATTEMPTS),
            reraise=True,
        ):
            with attempt:
                response = await self._client().models.embed_content(
                    model=self.model, contents=self._content(text), config=config
                )
        embeddings = response.embeddings or []
        if len(embeddings) != 1 or not embeddings[0].values:
            raise ValueError(f"expected one embedding, got {len(embeddings)}")
        return list(embeddings[0].values)


# --- explanations --------------------------------------------------------------------


class GeminiExplainer:
    provider = NAME
    pricing = EXPLAIN_PRICING

    def __init__(self, sdk: Any, model: str = EXPLAIN_MODEL) -> None:
        self.client = sdk  # google.genai async client (`Client(...).aio`)
        self.model = model

    async def generate(self, system: str, prompt: str) -> Generated:
        response = await self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "system_instruction": system,
                "max_output_tokens": EXPLAIN_MAX_OUTPUT_TOKENS,
                "thinking_config": {"thinking_level": THINKING_LEVEL},
            },
        )
        return Generated(
            text=response.text or "", usage=_usage(getattr(response, "usage_metadata", None))
        )


# --- the provider --------------------------------------------------------------------

_explainers: dict[str, GeminiExplainer] = {}


class GeminiProvider:
    name = NAME

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def trait_extractor(self) -> GeminiTraitExtractor:
        return GeminiTraitExtractor(self._settings)

    def trait_scorer(self) -> GeminiTraitScorer:
        return GeminiTraitScorer(self._settings)

    def embedder(self, dim: int) -> GeminiEmbedder:
        return GeminiEmbedder(self._settings, dim)

    def explainer(self) -> Explainer | None:
        """One client per process per key, not one per request."""
        key = self._settings.gemini_api_key
        if not key:
            return None
        if key not in _explainers:
            _explainers[key] = GeminiExplainer(genai.Client(api_key=key).aio)
        return _explainers[key]
