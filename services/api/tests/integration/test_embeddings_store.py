"""Embedding storage with a fake embedder. No provider, no network."""

from collections.abc import Sequence

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EMBEDDING_DIM, MovieEmbedding, MovieTraits
from app.pipelines.embeddings import embed_films, select_pending
from app.pipelines.ingest import SqlIngestStore
from app.pipelines.tmdb import to_film_record
from app.traits import TRAIT_KEYS, to_vector
from tests.conftest import load_fixture


class FakeEmbedder:
    model = "fake-embedder"
    dim = EMBEDDING_DIM

    def __init__(self, *, short_by: int = 0) -> None:
        self.texts: list[str] = []
        self._short_by = short_by

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.texts.extend(texts)
        return [[float(len(t))] + [0.0] * (self.dim - 1 - self._short_by) for t in texts]


@pytest.fixture
async def scored(db_session: AsyncSession) -> AsyncSession:
    store = SqlIngestStore(db_session)
    await store.upsert_film(to_film_record(load_fixture("tmdb_movie_550.json")))
    await store.upsert_film(to_film_record({"id": 7_000_001, "title": "No traits yet"}))
    scores = {key: 50.0 for key in TRAIT_KEYS}
    db_session.add(
        MovieTraits(
            movie_id=550,
            scores=scores,
            vector=to_vector(scores),
            summary="For viewers who like a film that argues with them.",
            model="fixture",
        )
    )
    await db_session.flush()
    return db_session


async def test_only_films_with_traits_are_pending(scored: AsyncSession) -> None:
    pending = dict(await select_pending(scored, limit=10_000))
    assert pending[550] == "For viewers who like a film that argues with them."
    assert 7_000_001 not in pending


async def test_embeddings_are_stored_from_the_built_text(scored: AsyncSession) -> None:
    embedder = FakeEmbedder()
    stored = await embed_films(scored, embedder, [(550, "For viewers who argue.")])

    assert stored == 1
    assert "Title: Fight Club (1999)" in embedder.texts[0]
    assert "For viewers: For viewers who argue." in embedder.texts[0]
    row = await scored.get(MovieEmbedding, 550)
    assert row is not None
    assert row.model == "fake-embedder"
    assert len(row.embedding) == EMBEDDING_DIM
    assert 550 not in dict(await select_pending(scored, limit=10_000))


async def test_re_embedding_replaces_the_vector(scored: AsyncSession) -> None:
    await embed_films(scored, FakeEmbedder(), [(550, "short")])
    await embed_films(scored, FakeEmbedder(), [(550, "a much longer summary than before")])
    row = await scored.get(MovieEmbedding, 550, populate_existing=True)
    assert row is not None
    first_component = float(row.embedding[0])
    assert first_component > 100  # length of the longer text, not the first one


async def test_wrong_sized_vectors_are_rejected(scored: AsyncSession) -> None:
    with pytest.raises(ValueError, match="-d vector"):
        await embed_films(scored, FakeEmbedder(short_by=1), [(550, None)])
