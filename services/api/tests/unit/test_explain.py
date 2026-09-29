"""The explanation prompt, the answer check, and the Gemini call shape. No network."""

from datetime import date
from types import SimpleNamespace

from app.models import Movie
from app.services.explain import MAX_CHARS, GeminiExplainer, build_prompt, clean
from app.traits import TRAIT_KEYS


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
            return SimpleNamespace(text="Because.")

    explainer = GeminiExplainer(SimpleNamespace(models=Models()))
    assert await explainer.generate("the prompt") == "Because."
    (call,) = calls
    assert call["model"] == "gemini-3.5-flash-lite"
    assert call["contents"] == "the prompt"
    assert call["config"]["thinking_config"] == {"thinking_level": "MINIMAL"}  # type: ignore[index]


async def test_an_empty_answer_is_an_empty_string() -> None:
    class Models:
        async def generate_content(self, **kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(text=None)

    assert await GeminiExplainer(SimpleNamespace(models=Models())).generate("p") == ""


def test_the_client_is_built_once_per_key() -> None:
    from app.config import Settings
    from app.deps import _explainer, get_explainer

    _explainer.cache_clear()
    first = get_explainer(Settings(_env_file=None, gemini_api_key="fake-key-not-used"))
    second = get_explainer(Settings(_env_file=None, gemini_api_key="fake-key-not-used"))
    assert first is second
    assert get_explainer(Settings(_env_file=None, gemini_api_key="")) is None
    _explainer.cache_clear()
