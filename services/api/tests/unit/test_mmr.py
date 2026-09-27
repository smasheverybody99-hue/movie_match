"""MMR trades a little relevance for variety."""

from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from app.services.mmr import mmr


@dataclass(frozen=True)
class Film:
    name: str
    relevance: float
    kind: str  # films of the same kind are near-duplicates


def _similarity(a: Film, b: Film) -> float:
    return 0.95 if a.kind == b.kind else 0.1


FILMS = [
    Film("Dark Knight", 0.95, "batman"),
    Film("Dark Knight Rises", 0.93, "batman"),  # near-duplicate of the first
    Film("Memento", 0.90, "puzzle"),
]


def _run(films: list[Film], k: int, lambda_: float = 0.7) -> list[str]:
    return [f.name for f in mmr(films, lambda f: f.relevance, _similarity, k, lambda_)]


def test_a_near_duplicate_loses_to_a_different_film() -> None:
    # step 2: Rises 0.7·0.93 - 0.3·0.95 = 0.366; Memento 0.7·0.90 - 0.3·0.1 = 0.600
    assert _run(FILMS, k=2) == ["Dark Knight", "Memento"]


def test_the_duplicate_still_comes_when_there_is_room() -> None:
    assert _run(FILMS, k=3) == ["Dark Knight", "Memento", "Dark Knight Rises"]


def test_lambda_one_is_plain_relevance_order() -> None:
    assert _run(FILMS, k=3, lambda_=1.0) == ["Dark Knight", "Dark Knight Rises", "Memento"]


def test_ties_go_to_the_earlier_candidate() -> None:
    films = [Film("A", 0.8, "x"), Film("B", 0.8, "y")]
    assert _run(films, k=1) == ["A"]


def test_k_and_empty_input() -> None:
    assert _run(FILMS, k=0) == []
    assert _run([], k=5) == []
    assert len(_run(FILMS, k=10)) == 3


def test_lambda_out_of_range_is_rejected() -> None:
    with pytest.raises(ValueError):
        _run(FILMS, k=1, lambda_=1.5)


def test_an_inadmissible_candidate_is_skipped() -> None:
    # at most one film of each kind: Rises is vetoed even though there is room
    def one_per_kind(film: Film, picked: Sequence[Film]) -> bool:
        return all(film.kind != p.kind for p in picked)

    picked = mmr(FILMS, lambda f: f.relevance, _similarity, 3, admissible=one_per_kind)
    assert [f.name for f in picked] == ["Dark Knight", "Memento"]
