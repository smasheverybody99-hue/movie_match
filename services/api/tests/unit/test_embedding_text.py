"""Embedding text is deterministic and carries the fields retrieval depends on."""

import pytest

from app.config import Settings
from app.models import EMBEDDING_DIM
from app.pipelines.embeddings import (
    MAX_KEYWORDS,
    build_embedding_text,
    embed_films,
    get_embedder,
)

FILM = {
    "id": 550,
    "title": "Fight Club",
    "year": 1999,
    "genres": ["Thriller", "Drama"],
    "keywords": ["nihilism", "dual identity", "support group"],
    "overview": "An insomniac and a soap salesman\n start an underground club.",
}
SUMMARY = "For viewers who like a film that argues with them."


def test_same_input_same_text() -> None:
    assert build_embedding_text(FILM, SUMMARY) == build_embedding_text(dict(FILM), SUMMARY)


def test_list_order_does_not_change_the_text() -> None:
    shuffled = {
        **FILM,
        "genres": ["Drama", "Thriller"],
        "keywords": list(reversed(FILM["keywords"])),
    }
    assert build_embedding_text(shuffled, SUMMARY) == build_embedding_text(FILM, SUMMARY)


def test_includes_title_year_genres_keywords_overview_and_summary() -> None:
    text = build_embedding_text(FILM, SUMMARY)
    assert "Title: Fight Club (1999)" in text
    assert "Genres: Drama, Thriller" in text
    assert "Keywords: dual identity, nihilism, support group" in text
    assert "Overview: An insomniac and a soap salesman start an underground club." in text
    assert f"For viewers: {SUMMARY}" in text


def test_missing_fields_are_left_out() -> None:
    text = build_embedding_text({"id": 1, "title": "Untitled"}, None)
    assert text == "Title: Untitled"


def test_keywords_are_capped() -> None:
    film = {**FILM, "keywords": [f"kw{i:03d}" for i in range(MAX_KEYWORDS + 20)]}
    line = next(x for x in build_embedding_text(film, None).splitlines() if x.startswith("Key"))
    assert len(line.removeprefix("Keywords: ").split(", ")) == MAX_KEYWORDS


def test_no_key_means_no_embedder() -> None:
    """Without GEMINI_API_KEY nothing can reach a paid API by accident."""
    with pytest.raises(SystemExit, match="GEMINI_API_KEY"):
        get_embedder(Settings(_env_file=None, gemini_api_key=""))


class _WrongSize:
    model = "fake"
    dim = EMBEDDING_DIM + 1

    async def embed(self, texts: object) -> list[list[float]]:
        raise AssertionError("must be rejected before any call")


async def test_embedder_of_wrong_dimension_is_rejected() -> None:
    with pytest.raises(ValueError, match="-d"):
        await embed_films(None, _WrongSize(), [(1, None)])  # type: ignore[arg-type]
