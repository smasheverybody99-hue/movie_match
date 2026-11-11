"""The tool schema the model is given matches what search_movies accepts."""

import inspect

from app.providers.gemini import chat_config
from app.services import assistant
from app.services.assistant import (
    MOODS,
    TOOL,
    SearchArgs,
    parse_args,
    search_movies,
    search_request,
    tool_schema,
)
from app.traits import TRAIT_KEYS

# Server-side only: the films the conversation has shown, added whatever the model says.
SERVER_ONLY = {"session", "user_id", "shown"}


def test_the_schemas_properties_are_search_movies_keyword_arguments() -> None:
    parameters = inspect.signature(search_movies).parameters
    accepted = {name for name in parameters if name not in SERVER_ONLY}
    assert set(tool_schema()["properties"]) == accepted
    assert accepted == {"traits", "year_min", "year_max", "runtime_max", "mood", "exclude_ids"}
    for name in accepted:
        assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert parameters[name].default is None  # every argument is optional


def test_trait_properties_are_the_shared_vocabulary_in_order() -> None:
    traits = tool_schema()["properties"]["traits"]["properties"]
    assert tuple(traits) == TRAIT_KEYS
    for spec in traits.values():
        assert (spec["type"], spec["minimum"], spec["maximum"]) == ("integer", 0, 100)
        assert spec["description"]


def test_moods_are_the_enum_and_only_name_real_traits() -> None:
    mood = tool_schema()["properties"]["mood"]
    assert mood["enum"] == sorted(MOODS)
    for levels in MOODS.values():
        assert set(levels) <= set(TRAIT_KEYS)
        assert all(0 <= v <= 100 for v in levels.values())


def test_every_value_the_schema_allows_is_accepted_unchanged() -> None:
    props = tool_schema()["properties"]
    raw = {
        "traits": {key: 100 for key in TRAIT_KEYS},
        "year_min": props["year_min"]["minimum"],
        "year_max": props["year_max"]["maximum"],
        "runtime_max": props["runtime_max"]["minimum"],
        "mood": props["mood"]["enum"][0],
        "exclude_ids": [1, 2],
    }
    args = parse_args(raw)
    assert args.dropped == ()
    assert args == SearchArgs(
        traits={key: 100.0 for key in TRAIT_KEYS},
        year_min=raw["year_min"],
        year_max=raw["year_max"],
        runtime_max=raw["runtime_max"],
        mood=raw["mood"],
        exclude_ids=frozenset({1, 2}),
    )


def test_what_the_schema_forbids_is_dropped_not_guessed() -> None:
    args = parse_args(
        {
            "traits": {"humor": 101, "plot_twist": 70.5, "made_up": 50, "mystery": True},
            "year_min": 1800,
            "runtime_max": "90",
            "mood": "sleepy",
            "exclude_ids": "1,2",
            "rank_by": "my favourites",
        }
    )
    assert args.traits == {}
    assert (args.year_min, args.runtime_max, args.mood) == (None, None, None)
    assert args.exclude_ids == frozenset()
    assert set(args.dropped) == {
        "traits.humor",
        "traits.plot_twist",
        "traits.made_up",
        "traits.mystery",
        "year_min",
        "runtime_max",
        "mood",
        "exclude_ids",
        "rank_by",
    }
    # Whole numbers sent as floats are fine (some providers send every number that way).
    assert parse_args({"runtime_max": 90.0, "traits": {"humor": 80.0}}).runtime_max == 90


def test_the_request_puts_explicit_traits_over_the_mood_and_excludes_shown_films() -> None:
    args = parse_args({"mood": "mind_bending", "traits": {"plot_twist": 60}, "exclude_ids": [7]})
    request = search_request(args, shown={8})
    assert request.targets == {"psychological_complexity": 80, "plot_twist": 60.0}
    assert request.exclude == frozenset({7, 8})


def test_the_provider_is_given_the_schema_unchanged() -> None:
    config = chat_config("system", [TOOL], allow_tools=True)
    (declaration,) = config["tools"][0]["function_declarations"]
    assert declaration["name"] == assistant.TOOL_NAME == "search_movies"
    assert declaration["parameters_json_schema"] == tool_schema()
    assert chat_config("system", [TOOL], allow_tools=False)["tool_config"] == {
        "function_calling_config": {"mode": "NONE"}
    }
