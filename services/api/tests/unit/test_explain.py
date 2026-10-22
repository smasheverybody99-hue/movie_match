"""The explanation prompt, the answer check, and the Gemini call shape. No network."""

from datetime import date
from types import SimpleNamespace
from typing import get_args

import pytest

from app import schemas
from app.models import Movie
from app.providers.gemini import EXPLAIN_MODEL, GeminiExplainer
from app.services.explain import (
    DIFFERENCE_SYSTEM_PROMPT,
    LANGUAGE_NAMES,
    MAX_CHARS,
    RUSSIAN_STYLE,
    SYSTEM_PROMPT,
    Explained,
    Lang,
    Reason,
    build_prompt,
    clean,
    system_prompt,
)
from app.services.matching import TraitNotes
from app.traits import TRAIT_KEYS, trait_labels


def _scores(**values: float) -> dict[str, float]:
    return {key: values.get(key, 10.0) for key in TRAIT_KEYS}


# The catalogue mean per trait, which the prompt shows as "a typical film".
TYPICAL = {key: 40.0 for key in TRAIT_KEYS} | {"plot_twist": 31.0}


def REASONS(*keys: str) -> TraitNotes:
    return TraitNotes("reason", keys)


def DIFFERENCES(*keys: str) -> TraitNotes:
    return TraitNotes("difference", keys)


def test_prompt_names_the_film_the_reasons_and_the_language() -> None:
    movie = Movie(id=1, title="Memento", release_date=date(2000, 9, 5))
    taste = _scores(plot_twist=88.4, mystery=70)
    film = _scores(plot_twist=95, mystery=81.6)
    prompt = build_prompt(movie, REASONS("plot_twist", "mystery"), taste, film, "uz", TYPICAL)
    assert prompt.startswith("Film: Memento (2000)\n")
    # with the typical film's value, so the model can say how this one differs
    assert (
        "- Plot twists: the viewer's taste 88/100, this film 95/100, a typical film 31/100\n"
        in prompt
    )
    assert (
        "- Mystery: the viewer's taste 70/100, this film 82/100, a typical film 40/100\n" in prompt
    )
    assert prompt.index("Plot twists") < prompt.index("Mystery")  # strongest first
    assert "Uzbek" in prompt
    assert "Romance" not in prompt  # only the real reasons


@pytest.mark.parametrize(
    ("lang", "name"), [("en", "English"), ("uz", "Uzbek (Latin script)"), ("ru", "Russian")]
)
def test_prompt_asks_for_each_language(lang: Lang, name: str) -> None:
    prompt = build_prompt(
        Movie(id=1, title="Heat"), REASONS("action"), _scores(), _scores(), lang, TYPICAL
    )
    assert f"\n\nWrite the sentences in {name}." in prompt
    assert "- Action:" in prompt  # the brief itself stays in English


@pytest.mark.parametrize("lang", ["en", "uz"])
def test_prompt_ends_with_the_language_outside_russian(lang: Lang) -> None:
    prompt = build_prompt(
        Movie(id=1, title="Heat"), REASONS("action"), _scores(), _scores(), lang, TYPICAL
    )
    assert prompt.endswith(f"Write the sentences in {LANGUAGE_NAMES[lang]}.")
    assert RUSSIAN_STYLE not in prompt


def test_russian_prompt_names_the_qualities_in_russian_and_asks_for_natural_russian() -> None:
    prompt = build_prompt(
        Movie(id=1, title="Heat"), REASONS("action", "pacing"), _scores(), _scores(), "ru", TYPICAL
    )
    # the interface's words, so "action" does not come back as "действие"
    assert "Name the qualities with these Russian words: Action = экшен; Pace = динамичность." in (
        prompt
    )
    assert prompt.endswith("\n" + RUSSIAN_STYLE)
    assert RUSSIAN_STYLE.startswith("Пиши естественным русским языком, используй букву ё")
    assert "Romance" not in prompt and "романтика" not in prompt  # only the real reasons


def test_the_reason_brief_asks_for_a_match_and_forbids_a_comparison() -> None:
    """The live contradiction of 2026-10-22: Up's panel read "Why it suits you" over "much
    gentler than you usually prefer". A reason is closeness since TZ 1.27, so the brief must
    ask for a match outright and name the comparison forms as forbidden - the old brief
    asked for "more than most films do", which is where that sentence came from."""
    brief = " ".join(SYSTEM_PROMPT.lower().split())
    assert "sits at the level this viewer looks for" in brief
    assert "every sentence says that the two match" in brief
    for forbidden in [
        "more than you",
        "less than you",
        "further than you",
        "gentler than",
        "darker than you usually",
        "unlike the films you pick",
    ]:
        assert forbidden in brief, forbidden
    assert "never write a comparison between the viewer and the film" in brief
    # Saying the film differs is the other side's job, and is named as forbidden here.
    assert "do not say the film differs from them in any way" in brief


def test_a_difference_is_briefed_as_a_difference_and_never_as_a_recommendation() -> None:
    """The reported bug of 2026-10-15: a film away from the taste still read as "you'll
    like this". The brief for that side must not let the model say so."""
    assert system_prompt("reason") is SYSTEM_PROMPT
    assert system_prompt("difference") is DIFFERENCE_SYSTEM_PROMPT
    brief = " ".join(DIFFERENCE_SYSTEM_PROMPT.lower().split())
    assert "how a film differs from what they usually go for" in brief
    # Each of these is named as something the sentence may not do.
    for forbidden in [
        "will like",
        "dislike",
        "should watch",
        "recommend",
        "warn them off",
        "change of pace",
        "surprise",
        "worth trying",
    ]:
        assert forbidden in brief, forbidden
    assert "do not say or imply that they will like it" in brief
    # And it must not carry the other side's framing.
    assert "suits" not in brief


def test_the_difference_brief_demands_the_comparison_in_every_sentence() -> None:
    """Two live sentences, 2026-10-16. Godzilla's compared ("deeper into dark and heavy
    dread than you usually look for"); Casablanca's only described the film ("keeps things
    surprisingly straightforward and wraps up neatly"), never mentioning the viewer, which
    is how a difference reads as a review. The brief now requires both halves, and forbids
    the words that judge the difference."""
    brief = " ".join(DIFFERENCE_SYSTEM_PROMPT.lower().split())
    assert "every sentence is a comparison and must carry both of its halves" in brief
    assert "what this viewer usually goes for" in brief
    assert "where this film sits against it" in brief
    # Said outright, so a film-only sentence is named as the failure it is.
    assert "a sentence that only describes the film has not done the job" in brief
    for judging in ["surprisingly", "refreshingly", "oddly", "sadly", "unfortunately"]:
        assert judging in brief, judging
    assert "a difference is neither good nor bad" in brief
    # The ban that answers the original report stands unchanged.
    assert "do not say or imply that they will like it" in brief

    prompt = build_prompt(
        Movie(id=1, title="Godzilla"),
        DIFFERENCES("humor", "darkness"),
        _scores(),
        _scores(),
        "en",
        TYPICAL,
    )
    assert "sits well away from this viewer's taste" in prompt
    assert "the viewer leaning the same way" not in prompt
    assert "- Humor:" in prompt and "- Tone darkness:" in prompt


def test_the_prompt_heading_follows_the_side() -> None:
    args = (_scores(), _scores(), "en", TYPICAL)
    movie = Movie(id=1, title="Heat")
    reason = build_prompt(movie, REASONS("action"), *args)
    difference = build_prompt(movie, DIFFERENCES("action"), *args)
    assert "sits at this viewer's own level" in reason
    assert "closest first" in reason  # the order the rule ranked them in (TZ 1.27)
    assert "sits at this viewer's own level" not in difference
    assert "well away from this viewer's taste" in difference


def test_the_service_and_the_api_accept_the_same_languages() -> None:
    assert get_args(Lang) == get_args(schemas.Lang) == ("en", "uz", "ru")
    assert set(LANGUAGE_NAMES) == set(get_args(Lang))


def test_the_service_and_the_api_name_the_same_reasons() -> None:
    assert get_args(Reason) == get_args(schemas.ExplanationReason)


def test_a_sentence_and_a_reason_never_come_together() -> None:
    assert Explained(text="a sentence").reason is None
    assert Explained(reason="failed").text is None
    assert Explained() == Explained(text=None, reason=None)


@pytest.mark.parametrize("lang", ["en", "uz", "ru"])
def test_every_language_has_a_label_for_every_trait(lang: str) -> None:
    labels = trait_labels(lang)
    assert list(labels) == list(TRAIT_KEYS)
    assert all(label.strip() for label in labels.values())


def test_prompt_without_a_release_date() -> None:
    movie = Movie(id=1, title="Untitled")
    assert build_prompt(movie, REASONS("humor"), _scores(), _scores(), "en", TYPICAL).startswith(
        "Film: Untitled\n"
    )


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
