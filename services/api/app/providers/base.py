"""What the product needs from an LLM provider, in the product's own terms.

Three jobs, three protocols:

* TraitExtractor - film prompt -> 14 trait scores as JSON text, as a background batch
* Embedder       - film text -> a vector of `dim` numbers
* Explainer      - one short "why you'll like this" answer while a user waits

Nothing here names a vendor. Prompts, parsing, storage, caching and cost limits live in
the pipelines and services; a provider only moves text in and text (or vectors) out,
and reports the tokens it used. Adding a provider is one module in app/providers/ and
one line in PROVIDERS (app/providers/__init__.py). See docs/decisions/0006.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class Usage:
    """Tokens one call or one run used. `estimated` when counted from characters because
    the provider did not report them; thinking tokens count as output (they bill as it)."""

    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated: bool = False

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            requests=self.requests + other.requests,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            estimated=self.estimated or other.estimated,
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

    def usd(self, usage: Usage) -> float:
        return (
            usage.input_tokens * self.input_usd_per_mtok
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


class UnsupportedDimension(ValueError):
    """The provider's embedding model cannot produce vectors of the configured size."""
