"""The provider seam: the registry, the neutral types, the cost line, and the trait
pipeline driven by a fake provider that has nothing to do with any vendor."""

import logging
from collections.abc import Sequence

import pytest

from app.config import Settings
from app.pipelines import traits
from app.providers import PROVIDERS, UnknownProvider, get_provider
from app.providers import usage as cost_log
from app.providers.base import (
    Embedded,
    Generated,
    Pricing,
    TraitAnswer,
    TraitBatchResult,
    TraitRequest,
    Usage,
)
from app.providers.gemini import GeminiProvider

RATES = Pricing(input_usd_per_mtok=2.0, output_usd_per_mtok=10.0, source="test rates")


class FakeExtractor:
    provider = "fake"
    model = "fake-traits-1"
    pricing = RATES

    def __init__(self) -> None:
        self.sent: list[TraitRequest] = []

    async def submit(self, requests: Sequence[TraitRequest]) -> str:
        self.sent.extend(requests)
        return "job-1"

    async def collect(self, job_id: str) -> TraitBatchResult:
        return TraitBatchResult(state="running", detail="queued")


class FakeEmbedder:
    provider = "fake"
    model = "fake-embed-1"
    pricing = RATES

    def __init__(self, dim: int) -> None:
        self.dim = dim

    async def embed(self, texts: Sequence[str]) -> Embedded:
        return Embedded([[0.0] * self.dim for _ in texts], Usage(requests=len(texts)))


class FakeExplainer:
    provider = "fake"
    model = "fake-explain-1"
    pricing = RATES

    async def generate(self, system: str, prompt: str) -> Generated:
        return Generated("Because.", Usage(requests=1, input_tokens=10, output_tokens=5))


class FakeProvider:
    name = "fake"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def trait_extractor(self) -> FakeExtractor:
        return FakeExtractor()

    def embedder(self, dim: int) -> FakeEmbedder:
        return FakeEmbedder(dim)

    def explainer(self) -> FakeExplainer:
        return FakeExplainer()


# --- registry ---------------------------------------------------------------------------


def test_the_default_provider_is_gemini() -> None:
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "gemini"
    assert isinstance(get_provider(settings), GeminiProvider)


def test_an_unknown_provider_is_a_clear_error() -> None:
    with pytest.raises(UnknownProvider, match=r"LLM_PROVIDER='nope'.*known: gemini"):
        get_provider(Settings(_env_file=None, llm_provider="nope"))


def test_a_new_provider_is_one_registry_line(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(PROVIDERS, "fake", FakeProvider)
    provider = get_provider(Settings(_env_file=None, llm_provider="fake"))
    assert provider.name == "fake"
    assert provider.embedder(1024).dim == 1024
    assert provider.trait_extractor().model == "fake-traits-1"


def test_gemini_builds_every_worker_without_a_key() -> None:
    provider = GeminiProvider(Settings(_env_file=None))
    assert provider.trait_extractor().pricing.input_usd_per_mtok > 0
    assert provider.embedder(1536).dim == 1536
    assert provider.explainer() is None  # explanations stay null without a key


# --- usage and cost -----------------------------------------------------------------


def test_usage_adds_up_and_stays_estimated_once_estimated() -> None:
    total = Usage(1, 100, 10) + Usage(2, 50, 5, estimated=True)
    assert total == Usage(3, 150, 15, estimated=True)


def test_cost_is_arithmetic_you_can_check_by_hand() -> None:
    # 1M in at $2 + 0.5M out at $10 = $7
    assert RATES.usd(Usage(1, 1_000_000, 500_000)) == pytest.approx(7.0)


def test_the_cost_line_is_the_same_shape_for_every_provider(
    caplog: pytest.LogCaptureFixture,
) -> None:
    cost_log.log.propagate = True  # let caplog see it even if configure() ran earlier
    with caplog.at_level(logging.INFO, logger="app.cost"):
        line = cost_log.record("traits", "fake", "fake-traits-1", Usage(50, 21_000, 12_500), RATES)
    assert line == (
        "run=traits provider=fake model=fake-traits-1 requests=50 input_tokens=21000 "
        'output_tokens=12500 usd=0.1670 tokens=reported pricing="test rates"'
    )
    assert any(r.getMessage() == line for r in caplog.records)


def test_an_estimated_count_says_so() -> None:
    line = cost_log.cost_line("embeddings", "fake", "m", Usage(1, 10, estimated=True), RATES)
    assert "tokens=estimated" in line


# --- the trait pipeline knows no vendor ---------------------------------------------


def test_the_dry_run_estimate_uses_the_providers_prices() -> None:
    film = {"id": 1, "title": "A film"}
    estimate = traits.estimate_cost([film], FakeExtractor.pricing)
    assert estimate.pricing is RATES
    assert estimate.usd == pytest.approx(
        (estimate.input_tokens * 2.0 + estimate.output_tokens * 10.0) / 1_000_000
    )


def test_answers_are_matched_to_films_by_key() -> None:
    request = traits.build_request({"id": 27205, "title": "Inception"})
    answer = TraitAnswer(key=request.key, text="{}", error=None)
    assert traits.movie_id_from(answer.key) == 27205
