"""Reading the streamed answer (AnswerFilter), the system prompt, and the reset time."""

from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from app.models import Movie
from app.providers.base import ProviderUnavailable, RateLimited, TransientError
from app.services.assistant import (
    INSTRUCTIONS,
    MAX_FOLLOWUPS,
    RETRY_DELAY_SECONDS,
    AnswerFilter,
    Card,
    Event,
    Refusal,
    Text,
    _Call,
    resets_at,
    retry_delay,
    system_prompt,
    timing_line,
    tool_result,
)
from app.services.matching import TraitNotes
from app.services.recommend import Hit, SearchResult
from app.traits import TRAIT_KEYS


def hit(movie_id: int) -> Hit:
    movie = Movie(id=movie_id, title=f"Film {movie_id}", release_date=date(2001, 1, 1))
    return Hit(movie=movie, match=80, band=None, notes=TraitNotes(), fit=90)


def run(chunks: list[str], allowed: tuple[int, ...] = (1, 2)) -> tuple[list[Event], AnswerFilter]:
    answer = AnswerFilter()
    answer.allow([hit(i) for i in allowed])
    out: list[Event] = []
    for chunk in chunks:
        out += answer.feed(chunk)
    out += answer.close()
    return out, answer


def texts(out: list[Event]) -> str:
    return "".join(e.text for e in out if isinstance(e, Text))


def cards(out: list[Event]) -> list[int]:
    return [e.hit.movie.id for e in out if isinstance(e, Card)]


def test_markers_split_across_chunks_still_become_cards_in_place() -> None:
    out, _ = run(["One. [", "[fi", "lm:1]] Two. [[film:", "2]] End."])
    assert [type(e).__name__ for e in out] == ["Text", "Card", "Text", "Card", "Text"]
    assert cards(out) == [1, 2]
    assert texts(out) == "One.  Two.  End."


def test_an_id_the_search_did_not_return_is_dropped_and_a_repeat_counts_once() -> None:
    out, answer = run(["[[film:1]] [[film:999]] [[film:1]] [[film:abc]]"])
    assert cards(out) == [1]
    assert answer.shown == [1]
    assert answer.dropped == ["film:999", "film:1", "film:abc"]


def test_no_film_counts_before_the_search_has_run() -> None:
    out, _ = run(["[[film:1]]"], allowed=())
    assert cards(out) == []


def test_follow_ups_are_collected_capped_and_never_shown_as_text() -> None:
    long = "x" * 81
    out, answer = run(
        ["Ok. [[ask: Something  shorter ]] [[ask:Older]] [[ask:Older]] ", f"[[ask:{long}]]"]
        + [f"[[ask:More {i}]]" for i in range(5)]
    )
    assert answer.followups == ["Something shorter", "Older", "More 0"]
    assert len(answer.followups) == MAX_FOLLOWUPS
    assert "ask" not in texts(out)


def test_off_topic_replaces_the_answer_and_ignores_the_rest() -> None:
    out, answer = run(["[[off_topic]] The capital is Canberra. [[film:1]]"])
    assert out == [Refusal("off_topic")]
    assert answer.refused == "off_topic"
    assert answer.shown == []


def test_an_unclosed_marker_is_dropped_at_the_end_and_a_lone_bracket_is_text() -> None:
    out, answer = run(["A [b] c [[film:1 and no end"])
    assert texts(out) == "A [b] c "
    assert answer.dropped == ["[[film:1 and no end"]
    out, _ = run(["costs [", "5]"])
    assert texts(out) == "costs [5]"


def test_reciting_the_instructions_is_cut_off_before_the_words_are_shown() -> None:
    words = INSTRUCTIONS.split()
    # The recital arrives a few words at a time; nothing from the eighth word on is shown.
    chunks = ["Sure: "] + [" ".join(words[i : i + 3]) + " " for i in range(0, 30, 3)]
    out, answer = run(chunks)
    assert answer.refused == "leak"
    assert out[-1] == Refusal("leak")
    shown = texts(out).split()
    assert len(shown) < 1 + 8  # "Sure:" and at most seven words of the recital


def test_an_ordinary_answer_is_not_mistaken_for_a_leak() -> None:
    out, answer = run(
        [
            "A tight thriller that keeps its reveal for the very end. [[film:1]] ",
            "And a calm one about two brothers on a long road trip. [[film:2]]",
        ]
    )
    assert answer.refused is None
    assert cards(out) == [1, 2]


def test_the_system_prompt_starts_with_the_fixed_block_and_holds_no_user_text() -> None:
    taste = dict.fromkeys(TRAIT_KEYS, 50.0)
    weights = dict.fromkeys(TRAIT_KEYS, 0.5)
    prompt = system_prompt(taste, weights, "uz")
    assert prompt.startswith(INSTRUCTIONS)  # the cacheable prefix comes first, unchanged
    assert "Uzbek" in prompt
    assert all(f"- {key}: 50" in prompt for key in TRAIT_KEYS)
    # Two viewers share the prefix byte for byte; only what follows it differs.
    other = system_prompt({**taste, "humor": 90.0}, weights, "uz")
    assert other != prompt and other.startswith(INSTRUCTIONS)
    assert "no taste profile" in system_prompt(None, None, "en")


def test_the_tool_result_carries_facts_and_no_ranking_numbers() -> None:
    long = replace(hit(1), movie=Movie(id=1, title="Long", overview="y" * 500, runtime_minutes=88))
    result = tool_result(SearchResult(rating_count=12, hits=[long, hit(2)]), {2: ["Drama"]})
    assert result["ratings_needed"] == 0
    first, second = result["films"]
    assert len(first["overview"]) == 240
    assert (first["year"], first["runtime_minutes"]) == (None, 88)
    assert second["genres"] == ["Drama"] and second["year"] == 2001
    assert "match" not in first and "fit" not in first
    assert tool_result(SearchResult(rating_count=4), {})["ratings_needed"] == 6


def test_the_day_resets_at_the_next_utc_midnight() -> None:
    assert resets_at(datetime(2026, 11, 11, 23, 59, tzinfo=UTC)) == datetime(
        2026, 11, 12, tzinfo=UTC
    )
    assert resets_at(datetime(2026, 12, 31, 0, 0, tzinfo=UTC)) == datetime(2027, 1, 1, tzinfo=UTC)


def test_going_back_to_a_saved_state_forgets_what_came_after() -> None:
    """A call that runs again reads its answer from where the filter stood before it."""
    answer = AnswerFilter()
    answer.allow([hit(1), hit(2)])
    saved = answer.state()
    answer.feed("Here. [[film:1]] And [[ask:More]]")
    assert answer.shown == [1] and answer.finished

    answer.restore(saved)
    assert (answer.shown, answer.followups, answer.answer) == ([], [], "")
    assert not answer.finished
    answer.feed("Again. [[film:1]]")
    assert answer.shown == [1]  # not dropped as a repeat
    answer.restore(saved)  # the saved copy itself was not changed by the second run
    assert answer.shown == [] and set(answer.allowed) == {1, 2}


@pytest.mark.parametrize(
    ("error", "delay"),
    [
        (TransientError("503 UNAVAILABLE"), RETRY_DELAY_SECONDS),
        (RateLimited("429", retry_after=1.5), 1.5),
        (RateLimited("429", retry_after=30), None),  # a long wait is not worth a user's time
        (RateLimited("429"), None),  # no hint: likely the day's quota
        (ProviderUnavailable("403"), None),
        (ValueError("bug"), None),
    ],
)
def test_only_a_brief_unavailability_is_tried_again(error: Exception, delay: float | None) -> None:
    assert retry_delay(error) == delay


def test_the_timing_line_names_every_stage_and_marks_one_that_did_not_run() -> None:
    first, second = _Call(seconds=1.234, retries=1), _Call()
    line = timing_line({"prepare": 0.3, "first_text": 2.5}, first, second, 2.6, "off_topic")
    assert line == (
        "prepare=0.30 first_call=1.23 search=- second_call=- first_text=2.50 "
        "total=2.60 retries=1 end=off_topic"
    )
