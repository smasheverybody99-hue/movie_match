"""The pure part of recommend.py: scoring, bands and the floor, the director cap, MMR, the
query."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models import Movie
from app.services.matching import BandCuts, ReasonRule, TraitStats
from app.services.recommend import (
    MAX_PER_DIRECTOR,
    POOL_FACTOR,
    Candidate,
    Scored,
    pick,
    score,
    shortlist,
    taste_embedding,
)
from app.services.taste import RatedFilm
from app.traits import TRAIT_COUNT

HALF = TRAIT_COUNT // 2
TASTE = [85.0] * HALF + [15.0] * HALF
UNIFORM = [1.0] * TRAIT_COUNT
# A catalogue centred on 50 with sd 20: the taste's high half stands out (z = 1.75).
RULE = ReasonRule(TraitStats((50.0,) * TRAIT_COUNT, (20.0,) * TRAIT_COUNT))
NOW = datetime(2026, 9, 27, tzinfo=UTC)


def near(offset: float) -> list[float]:
    return [85.0 - offset] * HALF + [15.0 + offset] * HALF


def film(movie_id: int, vector: list[float], *directors: int) -> Candidate:
    return Candidate(
        movie=Movie(id=movie_id, title=f"Film {movie_id}"),
        vector=vector,
        directors=frozenset(directors),
    )


CANDIDATES = [
    film(1, near(30)),  # raw 70
    film(2, near(0)),  # raw 100
    film(3, near(45)),  # raw 55
    film(4, [15.0] * HALF + [85.0] * HALF),  # opposite: raw 30
]
# As if the user's catalogue put place N at 100, its closest 35% at 70 and floor at 50.
CUTS = BandCuts(strong=100.0, good=70.0, floor=50.0)


def test_score_drops_below_the_floor_and_sorts_best_first() -> None:
    scored = score(CANDIDATES, TASTE, UNIFORM, RULE, CUTS)
    assert [(s.movie_id, s.match) for s in scored] == [(2, 100), (1, 70), (3, 55)]
    assert scored[0].reasons  # the high half, where the film stands out


def test_score_gives_each_film_its_band() -> None:
    scored = score(CANDIDATES, TASTE, UNIFORM, RULE, CUTS)
    assert [(s.movie_id, s.band) for s in scored] == [(2, "strong"), (1, "good"), (3, None)]


def test_without_cuts_nothing_is_dropped_and_nothing_has_a_band() -> None:
    scored = score(CANDIDATES, TASTE, UNIFORM, RULE)
    assert [s.movie_id for s in scored] == [2, 1, 3, 4]
    assert {s.band for s in scored} == {None}


def test_without_a_reason_rule_the_reasons_are_empty() -> None:
    (only,) = score([film(1, near(0))], TASTE, UNIFORM, None)
    assert (only.match, only.reasons) == (100, [])


def test_ties_on_match_go_to_the_lower_id() -> None:
    scored = score([film(9, near(5)), film(3, near(5))], TASTE, UNIFORM, RULE)
    assert [s.movie_id for s in scored] == [3, 9]


def _no_overlap(a: Scored, b: Scored) -> float:
    return 0.0


def test_director_cap() -> None:
    scored = score([film(i, near(i % 3), 77) for i in range(1, 6)], TASTE, UNIFORM, RULE)
    assert len(pick(scored, 10, _no_overlap)) == MAX_PER_DIRECTOR


def test_a_film_with_two_directors_counts_for_both() -> None:
    scored = score(
        [film(1, near(0), 1, 2), film(2, near(1), 1), film(3, near(2), 2), film(4, near(3), 1)],
        TASTE,
        UNIFORM,
        RULE,
    )
    # director 1 has films 1 and 2 once they are picked, so film 4 is out
    assert [s.movie_id for s in pick(scored, 10, _no_overlap)] == [1, 2, 3]


def test_shortlist_excludes_and_limits() -> None:
    scored = score([film(i, near(i)) for i in range(1, 11)], TASTE, UNIFORM, RULE)
    pool = shortlist(scored, k=2, exclude={1, 3})
    assert [s.movie_id for s in pool] == [2, 4, 5, 6, 7, 8][: POOL_FACTOR * 2]


def test_diversity_beats_a_near_duplicate() -> None:
    # 2 is a sequel of 1 (embeddings 0.97 alike); 3 matches a little less but is its own
    # film. step 2: film 2 0.7·0.99 - 0.3·0.97 = 0.402; film 3 0.7·0.95 - 0.3·0.2 = 0.605
    scored = score([film(1, near(0)), film(2, near(1)), film(3, near(5))], TASTE, UNIFORM, RULE)
    sims = {frozenset((1, 2)): 0.97, frozenset((1, 3)): 0.2, frozenset((2, 3)): 0.2}

    def similarity(a: Scored, b: Scored) -> float:
        return sims[frozenset((a.movie_id, b.movie_id))]

    assert [s.movie_id for s in pick(scored, 2, similarity)] == [1, 3]


def rated(score_: float, days_ago: float = 0) -> RatedFilm:
    return RatedFilm(score=score_, rated_at=NOW - timedelta(days=days_ago), vector=TASTE)


def test_taste_embedding_is_the_weighted_mean_of_unit_vectors() -> None:
    # weights: 9 -> 4, 7 -> 2; each embedding normalised first (length 2 and 3 here)
    films = [(rated(9), [2.0, 0.0]), (rated(7), [0.0, 3.0])]
    assert taste_embedding(films, NOW) == pytest.approx([4 / 6, 2 / 6])


def test_taste_embedding_ignores_disliked_and_zero_films() -> None:
    films = [(rated(4), [1.0, 0.0]), (rated(9), [0.0, 0.0]), (rated(8), [0.0, 5.0])]
    assert taste_embedding(films, NOW) == pytest.approx([0.0, 1.0])


def test_no_liked_film_means_no_query() -> None:
    assert taste_embedding([(rated(3), [1.0, 0.0])], NOW) is None
    assert taste_embedding([], NOW) is None
