"""The cost estimate is arithmetic you can check by hand."""

import math

import pytest

from app.pipelines import traits
from app.pipelines.traits import CostEstimate, build_prompt, estimate_cost


def test_usd_from_tokens_at_batch_rates() -> None:
    # 1M input at $0.50 + 1M output at $2.50
    assert CostEstimate(films=10, input_tokens=1_000_000, output_tokens=1_000_000).usd == 3.0


def test_estimate_counts_prompt_characters_and_expected_output() -> None:
    films = [{"id": 1, "title": "A"}, {"id": 2, "title": "Bee", "overview": "x" * 700}]
    chars = sum(len(traits.SYSTEM_PROMPT) + 20 + len(build_prompt(f)) for f in films)
    estimate = estimate_cost(films)
    assert estimate.films == 2
    assert estimate.input_tokens == math.ceil(chars / traits.CHARS_PER_TOKEN)
    assert estimate.output_tokens == 2 * traits.EXPECTED_OUTPUT_TOKENS


def test_scaling_keeps_per_film_averages() -> None:
    fifty = CostEstimate(films=50, input_tokens=20_000, output_tokens=12_500)
    full = fifty.scaled_to(5000)
    assert (full.films, full.input_tokens, full.output_tokens) == (5000, 2_000_000, 1_250_000)
    assert full.usd == pytest.approx(fifty.usd * 100)


def test_scaling_an_empty_estimate() -> None:
    assert CostEstimate(0, 0, 0).scaled_to(5000).usd == 0.0


def test_no_films_costs_nothing() -> None:
    assert estimate_cost([]).usd == 0.0
