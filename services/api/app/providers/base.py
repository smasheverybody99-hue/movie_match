"""What the product needs from an LLM provider, in the product's own terms.

Four jobs, four protocols:

* TraitExtractor - film prompt -> 14 trait scores as JSON text, as a background batch
* Embedder       - film text -> a vector of `dim` numbers
* Explainer      - one short "why you'll like this" answer while a user waits
* Assistant      - a streamed chat answer that may ask for one tool (ADR 0009)

Nothing here names a vendor. Prompts, parsing, storage, caching and cost limits live in
the pipelines and services; a provider only moves text in and text (or vectors) out,
and reports the tokens it used. Adding a provider is one module in app/providers/ and
one line in PROVIDERS (app/providers/__init__.py). See docs/decisions/0006.
"""

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class Usage:
    """Tokens one call or one run used. `estimated` when counted from characters because
    the provider did not report them; thinking tokens count as output (they bill as it).
    `cached_input_tokens` is the part of `input_tokens` the provider served from its
    prompt cache, which bills at the cache rate when the pricing has one."""

    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated: bool = False
    cached_input_tokens: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            requests=self.requests + other.requests,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            estimated=self.estimated or other.estimated,
            cached_input_tokens=self.cached_input_tokens + other.cached_input_tokens,
        )


@dataclass(frozen=True)
class Pricing:
    """USD per million tokens for one model in one mode (batch or standard).

    `source` says where the numbers came from and when they were checked, so a stale
    price is visible in every cost line that uses it (docs/costs.md).
    """

    input_usd_per_mtok: float
    output_usd_per_mtok: float
    source: str
    # Input tokens served from the provider's prompt cache. None: no cache rate, so cached
    # tokens bill like any other input (the conservative reading).
    cached_input_usd_per_mtok: float | None = None

    def usd(self, usage: Usage) -> float:
        cached = usage.cached_input_tokens if self.cached_input_usd_per_mtok is not None else 0
        return (
            (usage.input_tokens - cached) * self.input_usd_per_mtok
            + cached * (self.cached_input_usd_per_mtok or 0.0)
            + usage.output_tokens * self.output_usd_per_mtok
        ) / 1_000_000


# --- trait extraction ----------------------------------------------------------------


@dataclass(frozen=True)
class TraitRequest:
    """One film. `key` comes back on its answer; `schema` is the JSON the answer must match."""

    key: str
    system: str
    prompt: str
    schema: dict[str, Any]


JobState = Literal["running", "done", "failed", "cancelled", "expired"]


@dataclass(frozen=True)
class TraitAnswer:
    """One film's result: text to parse, or why there is none. Never both.

    `final` marks a refusal that asking again cannot change (the provider's safety filter
    blocked the prompt itself): the film is given up at once, not retried.
    """

    key: str
    text: str | None
    error: str | None
    usage: Usage = field(default_factory=Usage)
    final: bool = False


@dataclass(frozen=True)
class TraitBatchResult:
    """`state` in product terms; `detail` is the provider's own word for it, for messages.
    `answers` is empty unless the state is "done"."""

    state: JobState
    detail: str
    answers: list[TraitAnswer] = field(default_factory=list)


class TraitExtractor(Protocol):
    provider: str
    model: str
    pricing: Pricing  # what a batch run bills at

    async def submit(self, requests: Sequence[TraitRequest]) -> str:
        """Start a batch; returns its job id."""
        ...

    async def collect(self, job_id: str) -> TraitBatchResult: ...


class RateLimited(Exception):
    """The provider refused the request for its request rate or daily quota (HTTP 429).
    `retry_after` is the provider's own hint in seconds, when it gave one."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TransientError(Exception):
    """A server-side failure (5xx, timeout) worth one more try."""


class ProviderUnavailable(Exception):
    """The account cannot make this call at all (billing, permission, disabled API).
    Retrying or moving to the next film cannot help: the run stops."""


class TraitScorer(Protocol):
    """One film at a time through the provider's standard (not batch) API.

    For accounts where batch does not work (ADR 0006, amendment 2026-09-30). Raises
    RateLimited, TransientError or ProviderUnavailable; any other refusal of one film comes
    back as a TraitAnswer with `error`, like a failed item in a batch.
    """

    provider: str
    model: str
    pricing: Pricing  # the standard rate: sync requests are not discounted

    async def score(self, request: TraitRequest) -> TraitAnswer: ...


# --- embeddings ------------------------------------------------------------------------


@dataclass(frozen=True)
class Embedded:
    vectors: list[list[float]]  # one per text, in the order of the texts
    usage: Usage


class Embedder(Protocol):
    provider: str
    model: str
    dim: int
    pricing: Pricing

    async def embed(self, texts: Sequence[str]) -> Embedded: ...


# --- explanations ----------------------------------------------------------------------


@dataclass(frozen=True)
class Generated:
    text: str
    usage: Usage


class Explainer(Protocol):
    provider: str
    model: str
    pricing: Pricing  # standard (not batch) rate: a user is waiting

    async def generate(self, system: str, prompt: str) -> Generated: ...


# --- the assistant ---------------------------------------------------------------------


@dataclass(frozen=True)
class ToolSpec:
    """A function the model may ask for. `parameters` is the JSON Schema of its arguments."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    """The model asked for `name` with `args`.

    `raw` is the provider's own record of the call, sent back unchanged together with its
    result. Opaque here: Gemini 3 puts a thought signature on it that the next request must
    carry (ADR 0009); another provider may leave it None.
    """

    name: str
    args: dict[str, Any]
    raw: Any = None


ChatRole = Literal["user", "assistant", "tool"]


@dataclass(frozen=True)
class ChatMessage:
    """One message of the conversation in product terms.

    user      - `text` the person wrote
    assistant - `text` the model answered, or the `tool_call` it made
    tool      - the `result` of `tool_call`, which the product ran
    """

    role: ChatRole
    text: str = ""
    tool_call: ToolCall | None = None
    result: dict[str, Any] | None = None


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ToolRequested:
    call: ToolCall


# "interrupted": the stream broke off, and the error follows this event.
StopReason = Literal["done", "blocked", "truncated", "interrupted"]


@dataclass(frozen=True)
class StreamEnd:
    """The last event of every stream: what the call used, and how it ended. `detail` says
    why an answer did not end cleanly (the provider's own reason), for the log."""

    usage: Usage
    stop: StopReason = "done"
    detail: str = ""


AssistantEvent = TextDelta | ToolRequested | StreamEnd


class Assistant(Protocol):
    """One model call of the conversational assistant, streamed.

    Yields TextDelta and ToolRequested events as they arrive and always ends with one
    StreamEnd. With `allow_tools` False the model is told it may not call a tool (the
    answer after a tool result). Raises RateLimited, TransientError or ProviderUnavailable
    like the other workers; when the stream breaks off after it started, a StreamEnd with
    stop "interrupted" and the usage so far comes first, so the tokens are still counted.
    """

    provider: str
    model: str
    pricing: Pricing  # standard rate: a user is waiting

    def stream(
        self,
        system: str,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolSpec],
        *,
        allow_tools: bool,
    ) -> AsyncIterator[AssistantEvent]: ...


# --- the provider ----------------------------------------------------------------------


class Provider(Protocol):
    """Builds the three workers. Building must not need a key or the network, so a
    `--dry-run` can read prices without credentials; the first real call may."""

    name: str

    def trait_extractor(self) -> TraitExtractor: ...

    def trait_scorer(self) -> TraitScorer: ...

    def embedder(self, dim: int) -> Embedder:
        """Raises UnsupportedDimension if the model cannot produce `dim` numbers."""
        ...

    def explainer(self) -> Explainer | None:
        """None when explanations cannot be generated (no key): they then stay null."""
        ...

    def assistant(self) -> Assistant | None:
        """None when the assistant cannot answer (no key): the endpoint then says so."""
        ...


class UnsupportedDimension(ValueError):
    """The provider's embedding model cannot produce vectors of the configured size."""
