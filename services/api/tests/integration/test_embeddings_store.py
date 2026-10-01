"""Embedding runs against the test database with a fake, vendor-free embedder.

One film per request, paced; each vector committed as it arrives; a lost connection
resumes; the cost line is written in `finally` with a status (ADR 0006, 2026-10-01).
"""

from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EMBEDDING_DIM, MovieEmbedding, MovieTraits
from app.pipelines.embeddings import embed_films, run_embeddings, select_pending
from app.pipelines.ingest import SqlIngestStore
from app.pipelines.tmdb import to_film_record
from app.providers.base import (
    Embedded,
    Pricing,
    ProviderUnavailable,
    RateLimited,
    Usage,
)
from app.traits import TRAIT_KEYS, to_vector
from tests.conftest import load_fixture

FILMS = [550, 7_000_002, 7_000_003]  # all with traits; 7_000_001 has none


class FakeEmbedder:
    """Answers per film text from a script keyed by a word in the text: 'ok' by default,
    or an exception; a list is consumed one call at a time."""

    provider = "fake"
    model = "fake-embedder"
    dim = EMBEDDING_DIM
    pricing = Pricing(1.0, 0.0, "test rates")

    def __init__(self, *, short_by: int = 0, script: dict[str, Any] | None = None) -> None:
        self.texts: list[str] = []
        self._short_by = short_by
        self._script = script or {}

    async def embed(self, texts: Sequence[str]) -> Embedded:
        for text in texts:
            self.texts.append(text)
            for word, outcome in self._script.items():
                if word in text:
                    item = outcome.pop(0) if isinstance(outcome, list) else outcome
                    if isinstance(item, BaseException):
                        raise item
        vectors = [[float(len(t))] + [0.0] * (self.dim - 1 - self._short_by) for t in texts]
        return Embedded(vectors, Usage(requests=len(texts), input_tokens=10 * len(texts)))


class Sleeps:
    def __init__(self) -> None:
        self.waits: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.waits.append(seconds)


def _traits(session: AsyncSession, movie_id: int, summary: str) -> None:
    scores = {key: 50.0 for key in TRAIT_KEYS}
    session.add(
        MovieTraits(
            movie_id=movie_id,
            scores=scores,
            vector=to_vector(scores),
            summary=summary,
            model="fixture",
        )
    )


@pytest.fixture
async def scored(db_session: AsyncSession) -> AsyncSession:
    store = SqlIngestStore(db_session)
    await store.upsert_film(to_film_record(load_fixture("tmdb_movie_550.json")))
    await store.upsert_film(to_film_record({"id": 7_000_001, "title": "No traits yet"}))
    for movie_id, title in ((7_000_002, "Second Film"), (7_000_003, "Third Film")):
        await store.upsert_film(to_film_record({"id": movie_id, "title": title}))
    _traits(db_session, 550, "For viewers who like a film that argues with them.")
    _traits(db_session, 7_000_002, "For second-film viewers.")
    _traits(db_session, 7_000_003, "For third-film viewers.")
    await db_session.flush()
    return db_session


async def _embed(session: AsyncSession, embedder: FakeEmbedder, ids: Sequence[int], sleep=None):  # type: ignore[no-untyped-def]
    pending = await select_pending(session, 100, ids)
    return await embed_films(
        session, embedder, pending, requests_per_minute=20, retries=2, sleep=sleep or Sleeps()
    )


# --- selection ----------------------------------------------------------------------


async def test_only_films_with_traits_are_pending(scored: AsyncSession) -> None:
    pending = dict(await select_pending(scored, limit=10_000))
    assert pending[550] == "For viewers who like a film that argues with them."
    assert 7_000_001 not in pending


async def test_a_list_is_taken_in_its_order_skipping_what_is_not_pending(
    scored: AsyncSession,
) -> None:
    pending = await select_pending(scored, 100, [7_000_003, 7_000_001, 550])
    assert [movie_id for movie_id, _ in pending] == [7_000_003, 550]


# --- embed_films ----------------------------------------------------------------------


async def test_embeddings_are_stored_from_the_built_text_one_paced_request_each(
    scored: AsyncSession,
) -> None:
    embedder, sleep = FakeEmbedder(), Sleeps()
    result = await _embed(scored, embedder, FILMS, sleep)

    assert (result.stored, result.stopped) == (3, None)
    assert (result.usage.requests, result.usage.input_tokens) == (3, 30)
    assert "Title: Fight Club (1999)" in embedder.texts[0]
    assert "For viewers: For viewers who like a film" in embedder.texts[0]
    assert sleep.waits == [3.0, 3.0]  # 60/20 s between requests, none before the first
    row = await scored.get(MovieEmbedding, 550)
    assert row is not None and row.model == "fake-embedder"
    assert len(row.embedding) == EMBEDDING_DIM
    assert await select_pending(scored, 100, FILMS) == []


async def test_re_embedding_replaces_the_vector(scored: AsyncSession) -> None:
    common = {"requests_per_minute": 20, "retries": 0, "sleep": Sleeps()}
    await embed_films(scored, FakeEmbedder(), [(550, "short")], **common)
    await embed_films(
        scored, FakeEmbedder(), [(550, "a much longer summary than before")], **common
    )
    row = await scored.get(MovieEmbedding, 550, populate_existing=True)
    assert row is not None
    assert float(row.embedding[0]) > 100  # length of the longer text, not the first one


async def test_wrong_sized_vectors_are_rejected(scored: AsyncSession) -> None:
    with pytest.raises(ValueError, match="-d vector"):
        await _embed(scored, FakeEmbedder(short_by=1), [550])


async def test_a_rate_limit_past_its_retries_stops_and_keeps_the_rest_pending(
    scored: AsyncSession,
) -> None:
    quota = RateLimited("429 RESOURCE_EXHAUSTED", retry_after=30)
    sleep = Sleeps()
    result = await _embed(scored, FakeEmbedder(script={"Second Film": quota}), FILMS, sleep)

    assert result.stored == 1
    assert result.stopped is not None and "2 films left pending" in result.stopped
    assert sleep.waits == [3.0, 30, 30]  # pace, then the hint twice (retries=2)
    assert [m for m, _ in await select_pending(scored, 100, FILMS)] == FILMS[1:]


async def test_an_account_refusal_stops_at_once(scored: AsyncSession) -> None:
    embedder = FakeEmbedder(script={"Second Film": ProviderUnavailable("400 FAILED_PRECONDITION")})
    result = await _embed(scored, embedder, FILMS)
    assert result.stored == 1
    assert result.stopped is not None and "FAILED_PRECONDITION" in result.stopped
    assert not any("Third Film" in text for text in embedder.texts)  # nothing more sent


# --- run_embeddings: reconnecting, and the cost line in finally ----------------------


async def _run(session: AsyncSession, embedder: FakeEmbedder, **kwargs: Any):  # type: ignore[no-untyped-def]
    opened = {"n": 0}

    @asynccontextmanager
    async def open_session():  # type: ignore[no-untyped-def]
        opened["n"] += 1
        yield session

    lines: list[str] = []
    try:
        result = await run_embeddings(
            embedder,
            limit=100,
            ids=FILMS,
            requests_per_minute=20,
            retries=1,
            open_session=open_session,
            reconnect_delays=kwargs.pop("reconnect_delays", (1.0, 1.0)),
            sleep=Sleeps(),
            report=lines.append,
        )
    except BaseException as exc:
        return None, exc, lines, opened["n"]
    return result, None, lines, opened["n"]


def _cost_line(lines: list[str]) -> str:
    return next(line for line in lines if line.startswith("run=embeddings"))


async def test_a_lost_connection_reconnects_and_continues(scored: AsyncSession) -> None:
    drop = ConnectionResetError("connection was closed")
    embedder = FakeEmbedder(script={"Second Film": [drop, "ok"]})
    result, error, lines, attempts = await _run(scored, embedder)

    assert error is None and result is not None and result.stored == 3
    assert attempts == 2
    asked = [t.split("\n")[0] for t in embedder.texts]
    assert asked.count("Title: Second Film") == 2 and asked.count("Title: Fight Club (1999)") == 1
    assert any(line.startswith("connection lost (ConnectionResetError)") for line in lines)
    cost = _cost_line(lines)
    assert "status=complete" in cost and "requests=3 input_tokens=30" in cost
    assert "tokens=reported" in cost


async def test_an_interrupted_run_still_writes_its_cost_line(scored: AsyncSession) -> None:
    embedder = FakeEmbedder(script={"Third Film": RuntimeError("a bug, not a connection")})
    result, error, lines, _ = await _run(scored, embedder)

    assert result is None and isinstance(error, RuntimeError)
    assert "stored 2 embeddings" in lines
    cost = _cost_line(lines)
    assert "status=interrupted" in cost and "requests=2 input_tokens=20" in cost


async def test_an_account_refusal_is_reported_as_stopped(scored: AsyncSession) -> None:
    embedder = FakeEmbedder(script={"Fight Club": ProviderUnavailable("400 FAILED_PRECONDITION")})
    result, error, lines, _ = await _run(scored, embedder)
    assert error is None and result is not None and result.stopped
    assert "status=stopped" in _cost_line(lines)
