"""TMDB payload -> our shapes. The translation boundary must be exact and must not crash."""

from datetime import date

from app.pipelines.tmdb import CAST_LIMIT, to_candidate, to_film_record, to_movie_fields
from tests.conftest import load_fixture


def test_recorded_payload_maps_to_movie_fields() -> None:
    fields = to_movie_fields(load_fixture("tmdb_movie_550.json"))

    assert fields["id"] == 550
    assert fields["title"] == "Fight Club"
    assert fields["original_title"] == "Fight Club"
    assert fields["release_date"] == date(1999, 10, 15)
    assert fields["runtime_minutes"] == 139
    assert fields["original_language"] == "en"
    assert fields["poster_path"] == "/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg"
    assert fields["tmdb_vote_count"] == 32909
    assert fields["adult"] is False
    assert fields["overview"].startswith("A ticking-time-bomb insomniac")


def test_only_movie_columns_are_produced() -> None:
    """Budget, revenue, tagline etc. stay at the boundary; they are not our columns."""
    fields = to_movie_fields(load_fixture("tmdb_movie_550.json"))
    assert set(fields) == {
        "id",
        "title",
        "original_title",
        "overview",
        "release_date",
        "runtime_minutes",
        "original_language",
        "poster_path",
        "backdrop_path",
        "tmdb_vote_average",
        "tmdb_vote_count",
        "popularity",
        "adult",
    }


def test_genres_keywords_and_people() -> None:
    record = to_film_record(load_fixture("tmdb_movie_550.json"))

    assert record.genres == [(18, "Drama"), (53, "Thriller")]
    assert (1541, "nihilism") in record.keywords
    assert len(record.keywords) == 14

    director = [c for c in record.credits if c["job"] == "Director"]
    assert [c["person_id"] for c in director] == [7467]
    assert director[0]["department"] == "directing"

    cast = [c for c in record.credits if c["department"] == "cast"]
    assert [c["character_name"] for c in cast[:2]] == ["Narrator", "Tyler Durden"]
    assert [c["billing_order"] for c in cast] == sorted(c["billing_order"] for c in cast)


def test_recorded_cast_of_76_is_capped() -> None:
    record = to_film_record(load_fixture("tmdb_movie_550.json"))
    assert len([c for c in record.credits if c["department"] == "cast"]) == CAST_LIMIT


def test_crew_is_limited_to_story_jobs() -> None:
    """Producer, cinematographer and the novelist are dropped; screenplay is kept."""
    record = to_film_record(load_fixture("tmdb_movie_550.json"))
    jobs = {c["job"] for c in record.credits if c["department"] != "cast"}
    assert jobs == {"Director", "Screenplay"}


def test_every_credited_person_is_present_once() -> None:
    record = to_film_record(load_fixture("tmdb_movie_550.json"))
    people_ids = [p["id"] for p in record.people]
    assert len(people_ids) == len(set(people_ids))
    assert {c["person_id"] for c in record.credits} == set(people_ids)


def test_cast_is_capped_and_ordered_by_billing() -> None:
    payload = {
        "id": 1,
        "title": "Crowd",
        "credits": {
            "cast": [
                {"id": 100 + i, "name": f"Actor {i}", "order": 40 - i}
                for i in range(CAST_LIMIT + 10)
            ]
        },
    }
    cast = to_film_record(payload).credits
    assert len(cast) == CAST_LIMIT
    assert cast[0]["billing_order"] == 40 - (CAST_LIMIT + 9)  # lowest order first


def test_missing_optional_fields_do_not_crash() -> None:
    record = to_film_record({"id": 42})

    assert record.movie["id"] == 42
    assert record.movie["title"] == ""
    assert record.movie["release_date"] is None
    assert record.movie["runtime_minutes"] is None
    assert record.movie["overview"] is None
    assert record.genres == [] and record.keywords == []
    assert record.people == [] and record.credits == []


def test_empty_and_malformed_dates_become_none() -> None:
    assert to_movie_fields({"id": 1, "release_date": ""})["release_date"] is None
    assert to_movie_fields({"id": 1, "release_date": "1999-13-45"})["release_date"] is None


def test_zero_runtime_is_unknown_not_zero() -> None:
    """TMDB reports 0 when it does not know the runtime."""
    assert to_movie_fields({"id": 1, "runtime": 0})["runtime_minutes"] is None


def test_title_falls_back_to_original_title() -> None:
    assert to_movie_fields({"id": 1, "original_title": "Amélie"})["title"] == "Amélie"


def test_discover_result_maps_to_candidate() -> None:
    candidate = to_candidate(
        {
            "id": 129,
            "popularity": 98.5,
            "original_language": "ja",
            "release_date": "2001-07-20",
            "vote_count": 17000,
        }
    )
    assert candidate.id == 129
    assert candidate.language == "ja"
    assert candidate.year == 2001
    assert candidate.popularity == 98.5
    assert candidate.vote_count == 17000


def test_candidate_without_date_or_language() -> None:
    candidate = to_candidate({"id": 5})
    assert candidate.year is None
    assert candidate.language == "xx"
    assert candidate.popularity == 0.0
