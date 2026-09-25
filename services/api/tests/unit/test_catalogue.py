"""Catalogue selection: decade quotas, a language cap, popularity inside the constraints."""

import pytest

from app.pipelines.catalogue import (
    DECADE_WEIGHTS,
    build_pools,
    decade_quotas,
    pick_decade,
    select_catalogue,
)
from app.pipelines.tmdb import Candidate


def _c(film_id: int, language: str, popularity: float, year: int = 1995) -> Candidate:
    return Candidate(
        id=film_id, popularity=popularity, language=language, year=year, vote_count=500
    )


@pytest.mark.parametrize("target", [1, 7, 100, 5000, 20000])
def test_quotas_sum_exactly_to_target(target: int) -> None:
    assert sum(decade_quotas(target).values()) == target


def test_quotas_follow_the_weights() -> None:
    quotas = decade_quotas(8000)  # weights sum to 80, so 100 films per weight unit
    assert quotas == {decade: weight * 100 for decade, weight in DECADE_WEIGHTS.items()}


def test_zero_target_gives_empty_quotas() -> None:
    assert set(decade_quotas(0).values()) == {0}


def test_language_cap_holds_while_others_have_candidates() -> None:
    pool = [_c(i, "en", 100 - i) for i in range(10)] + [
        _c(100 + i, lang, 10 - i) for i, lang in enumerate(["fr", "ja", "ko", "it", "de"])
    ]
    picked = pick_decade(pool, quota=6, max_language_share=0.5)
    languages = [c.language for c in pool if c.id in picked]
    assert languages.count("en") == 3
    # The three most popular English films and the three most popular others.
    assert picked == [0, 1, 2, 100, 101, 102]


def test_cap_yields_when_the_pool_runs_out_of_other_languages() -> None:
    pool = [_c(i, "en", 100 - i) for i in range(10)] + [_c(99, "fr", 1)]
    picked = pick_decade(pool, quota=6, max_language_share=0.5)
    assert len(picked) == 6
    assert 99 in picked


def test_more_popular_wins_within_a_language() -> None:
    pool = [_c(1, "en", 5), _c(2, "en", 50), _c(3, "en", 20)]
    assert pick_decade(pool, quota=2, max_language_share=1.0) == [2, 3]


def test_small_pool_returns_what_it_has() -> None:
    assert pick_decade([_c(1, "en", 5)], quota=10, max_language_share=0.5) == [1]


def test_selection_has_no_duplicates_across_decades() -> None:
    shared = _c(7, "en", 99)
    pools = {1990: [shared, _c(8, "fr", 50)], 2000: [shared, _c(9, "ja", 40)]}
    weights = {1990: 1, 2000: 1}
    selection = select_catalogue(pools, target=4, max_language_share=1.0, weights=weights)
    assert len(selection.ids) == len(set(selection.ids))
    assert selection.ids == [7, 8, 9]
    assert selection.by_decade == {1990: 2, 2000: 1}
    assert selection.by_language == {"en": 1, "fr": 1, "ja": 1}


class FakeDiscover:
    """Serves `total_pages` pages of 20 candidates per decade and counts the calls."""

    def __init__(self, total_pages: int) -> None:
        self.total_pages = total_pages
        self.calls: list[tuple[int, int]] = []

    async def discover(self, *, page: int, year_from: int, year_to: int, min_votes: int):
        assert year_to == year_from + 9
        assert min_votes == 100
        self.calls.append((year_from, page))
        films = [_c(year_from * 1000 + page * 20 + i, "en", 1.0) for i in range(20)]
        return films, self.total_pages


async def test_pools_stop_once_they_have_enough() -> None:
    client = FakeDiscover(total_pages=50)
    weights = {1990: 1}
    pools = await build_pools(client, target=30, min_votes=100, weights=weights)  # type: ignore[arg-type]
    # 30 films x POOL_FACTOR 3 = 90 wanted -> 5 pages of 20.
    assert len(client.calls) == 5
    assert len(pools[1990]) == 100


async def test_pools_stop_at_the_last_page() -> None:
    client = FakeDiscover(total_pages=2)
    pools = await build_pools(client, target=300, min_votes=100, weights={1950: 1})  # type: ignore[arg-type]
    assert client.calls == [(1950, 1), (1950, 2)]
    assert len(pools[1950]) == 40
