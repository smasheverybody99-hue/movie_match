"""The explanation prompt, the answer check, and the Gemini call shape. No network."""

from datetime import date
from types import SimpleNamespace
from typing import get_args

import pytest

from app import schemas
from app.models import Movie
from app.providers.gemini import EXPLAIN_MODEL, GeminiExplainer
from app.services.explain import (
    LANGUAGE_NAMES,
    MAX_CHARS,
    SYSTEM_PROMPT,
    Lang,
    build_prompt,
    clean,
)
from app.traits import TRAIT_KEYS, trait_labels


def _scores(**values: float) -> dict[str, float]:
    return {key: values.get(key, 10.0) for key in TRAIT_KEYS}


def test_prompt_names_the_film_the_reasons_and_the_language() -> None:
    movie = Movie(id=1, title="Memento", release_date=date(2000, 9, 5))
    taste = _scores(plot_twist=88.4, mystery=70)
    film = _scores(plot_twist=95, mystery=81.6)
    prompt = build_prompt(movie, ["plot_twist", "mystery"], taste, film, "uz")
    assert prompt.startswith("Film: Memento (2000)\n")
    assert "- Plot twists: the viewer's taste 88/100, this film 95/100" in prompt
    assert "- Mystery: the viewer's taste 70/100, this film 82/100" in prompt
    assert prompt.index("Plot twists") < prompt.index("Mystery")  # strongest first
    assert "Uzbek" in prompt
    assert "Romance" not in prompt  # only the real reasons


@pytest.mark.parametrize(
    ("lang", "name"), [("en", "English"), ("uz", "Uzbek (Latin script)"), ("ru", "Russian")]
)
def test_prompt_asks_for_each_language(lang: Lang, name: str) -> None:
    prompt = build_prompt(Movie(id=1, title="Heat"), ["action"], _scores(), _scores(), lang)
    assert prompt.endswith(f"Write the sentences in {name}.")
    assert "- Action:" in prompt  # the brief itself stays in English


def test_the_service_and_the_api_accept_the_same_languages() -> None:
    assert get_args(Lang) == get_args(schemas.Lang) == ("en", "uz", "ru")
    assert set(LANGUAGE_NAMES) == set(get_args(Lang))


@pytest.mark.parametrize("lang", ["en", "uz", "ru"])
def test_every_language_has_a_label_for_every_trait(lang: str) -> None:
    labels = trait_labels(lang)
    assert list(labels) == list(TRAIT_KEYS)
    assert all(label.strip() for label in labels.values())


def test_prompt_without_a_release_date() -> None:
    movie = Movie(id=1, title="Untitled")
    assert build_prompt(movie, ["humor"], _scores(), _scores(), "en").startswith("Film: Untitled\n")


def test_clean() -> None:
    assert clean('  "Twisty and\n dark."  ') == "Twisty and dark."
    assert clean("   ") is None
    assert clean("x" * (MAX_CHARS + 1)) is None


async def test_gemini_explainer_sends_the_brief() -> None:
    calls: list[dict] = []

    class Models:
        async def generate_content(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            usage = SimpleNamespace(
                prompt_token_count=120, candidates_token_count=30, thoughts_token_count=5
            )
            return SimpleNamespace(text="Because.", usage_metadata=usage)

    explainer = GeminiExplainer(SimpleNamespace(models=Models()))
    generated = await explainer.generate(SYSTEM_PROMPT, "the prompt")
    assert generated.text == "Because."
    assert (generated.usage.input_tokens, generated.usage.output_tokens) == (120, 35)
    (call,) = calls
    assert call["model"] == EXPLAIN_MODEL == "gemini-3.5-flash-lite"
    assert call["contents"] == "the prompt"
    assert call["config"]["system_instruction"] == SYSTEM_PROMPT  # type: ignore[index]
    assert call["config"]["thinking_config"] == {"thinking_level": "MINIMAL"}  # type: ignore[index]


async def test_an_empty_answer_is_an_empty_string() -> None:
    class Models:
        async def generate_content(self, **kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(text=None)

    generated = await GeminiExplainer(SimpleNamespace(models=Models())).generate("s", "p")
    assert generated.text == ""
    assert generated.usage.requests == 1


def test_the_client_is_built_once_per_key() -> None:
    from app.config import Settings
    from app.deps import get_explainer

    first = get_explainer(Settings(_env_file=None, gemini_api_key="fake-key-not-used"))
    second = get_explainer(Settings(_env_file=None, gemini_api_key="fake-key-not-used"))
    assert first is not None and first is second
    assert get_explainer(Settings(_env_file=None, gemini_api_key="")) is None
