"""Sync trait runs against the test database with a fake, vendor-free scorer.

Each film is committed as it is answered, so a run stopped by a quota or an account
refusal resumes where it stopped (TRAIT_MODE=sync, ADR 0006 amendment 2026-09-30).
"""

import json
from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MovieTraits, TraitFailure
from app.pipelines.ingest import SqlIngestStore
from app.pipelines.tmdb import to_film_record
from app.pipelines.traits import load_films, run_sync, score_sync, select_pending
from app.providers.base import (
    Pricing,
    ProviderUnavailable,
    RateLimited,
    TraitAnswer,
    TraitRequest,
    Usage,
)
from app.traits import TRAIT_KEYS

IDS = [9_880_001, 9_880_002, 9_880_003, 9_880_004]


def valid_json(movie_id: int) -> str:
    scores = {key: (movie_id + i) % 101 for i, key in enumerate(TRAIT_KEYS)}
    return json.dumps({**scores, "summary": f"For viewers of film {movie_id}."})


class FakeScorer:
    """Answers per film from a script: 'ok', 'malformed', or an exception to raise."""

    provider = "fake"
    model = "fake-traits-sync-1"
    pricing = Pricing(1.0, 2.0, "test rates")

    def __init__(self, script: dict[int, Any] | None = None) -> None:
        self.script = script or {}
        self.asked: list[int] = []

    async def score(self, request: TraitRequest) -> TraitAnswer:
        movie_id = int(request.key.removeprefix("movie-"))
        self.asked.append(movie_id)
        outcome = self.script.get(movie_id, "ok")
        if isinstance(outcome, list):  # one entry per call: e.g. [OSError(...), "ok"]
            outcome = outcome.pop(0) if outcome else "ok"
        if isinstance(outcome, BaseException):
            raise outcome
        text = valid_json(movie_id) if outcome == "ok" else '{"humor": 5}'
        return TraitAnswer(request.key, text, None, Usage(1, 400, 200))


class Sleeps:
    def __init__(self) -> None:
        self.waits: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.waits.append(seconds)


@pytest.fixture
async def films(db_session: AsyncSession) -> AsyncSession:
    store = SqlIngestStore(db_session)
    for rank, movie_id in enumerate(IDS):
        await store.upsert_film(
            to_film_record({"id": movie_id, "title": f"Film {movie_id}", "popularity": 90 - rank})
        )
    return db_session


async def _run(
    session: AsyncSession, scorer: FakeScorer, ids: Sequence[int], sleep: Sleeps | None = None
):  # type: ignore[no-untyped-def]
    return await score_sync(
        session,
        scorer,
        await load_films(session, ids),
        requests_per_minute=10,
        retries=2,
        sleep=sleep or Sleeps(),
    )


async def test_each_film_is_stored_with_the_scorers_model(films: AsyncSession) -> None:
    sleep = Sleeps()
    result = await _run(films, FakeScorer(), IDS, sleep)

    assert (result.stored, result.failed, result.stopped) == (4, 0, None)
    assert (result.usage.requests, result.usage.input_tokens) == (4, 1600)
    traits = await films.get(MovieTraits, IDS[0])
    assert traits is not None and traits.model == "fake-traits-sync-1"
    assert set(traits.scores) == set(TRAIT_KEYS)
    # paced: one wait of 60/10 s between requests, none before the first
    assert sleep.waits == [6.0, 6.0, 6.0]


async def test_a_malformed_answer_is_a_counted_attempt(films: AsyncSession) -> None:
    result = await _run(films, FakeScorer({IDS[1]: "malformed"}), IDS)
    assert (result.stored, result.failed) == (3, 1)
    failure = await films.get(TraitFailure, IDS[1])
    assert failure is not None and failure.last_error.startswith("malformed: missing trait")
    assert await films.get(MovieTraits, IDS[1]) is None


async def test_an_account_refusal_stops_and_the_next_run_resumes(films: AsyncSession) -> None:
    refused = FakeScorer({IDS[2]: ProviderUnavailable("400 FAILED_PRECONDITION")})
    first = await _run(films, refused, IDS)
    assert (first.stored, first.failed) == (2, 0)
    assert first.stopped is not None and "FAILED_PRECONDITION" in first.stopped
    assert refused.asked == IDS[:3]  # nothing sent after the refusal
    assert await films.get(TraitFailure, IDS[2]) is None  # not the film's fault

    pending = await select_pending(films, 100, IDS)
    assert pending == IDS[2:]
    again = FakeScorer()
    second = await _run(films, again, pending)
    assert (second.stored, second.stopped) == (2, None)
    assert again.asked == IDS[2:]  # the two stored before are not asked again


async def test_a_quota_past_its_retries_stops_without_blaming_the_film(
    films: AsyncSession,
) -> None:
    quota = RateLimited("429 RESOURCE_EXHAUSTED: daily quota", retry_after=30)
    sleep = Sleeps()
    result = await _run(films, FakeScorer({IDS[1]: quota}), IDS, sleep)

    assert (result.stored, result.failed) == (1, 0)
    assert result.stopped is not None
    assert "3 films left pending" in result.stopped
    assert await films.get(TraitFailure, IDS[1]) is None
    assert sleep.waits == [6.0, 30, 30]  # pace, then the provider's hint twice (retries=2)
    assert await select_pending(films, 100, IDS) == IDS[1:]


# --- run_sync: reconnecting, and the cost line in finally --------------------------------


def _sessions(session: AsyncSession):  # type: ignore[no-untyped-def]
    """open_session for run_sync: every attempt gets the test's rolled-back session."""
    opened = {"n": 0}

    @asynccontextmanager
    async def open_session():  # type: ignore[no-untyped-def]
        opened["n"] += 1
        yield session

    return open_session, opened


async def _run_sync(session: AsyncSession, scorer: FakeScorer, **kwargs: Any):  # type: ignore[no-untyped-def]
    open_session, opened = _sessions(session)
    lines: list[str] = []
    try:
        result = await run_sync(
            IDS,
            scorer,
            requests_per_minute=10,
            retries=1,
            open_session=open_session,
            reconnect_delays=kwargs.pop("reconnect_delays", (1.0, 1.0)),
            sleep=Sleeps(),
            report=lines.append,
        )
    except BaseException as exc:  # the caller checks what was reported anyway
        return None, exc, lines, opened["n"]
    return result, None, lines, opened["n"]


def _cost_line(lines: list[str]) -> str:
    return next(line for line in lines if line.startswith("run=traits-sync"))


async def test_a_lost_connection_reconnects_and_continues_where_it_stopped(
    films: AsyncSession,
) -> None:
    scorer = FakeScorer({IDS[2]: [ConnectionResetError("connection was closed"), "ok"]})
    result, error, lines, attempts = await _run_sync(films, scorer)

    assert error is None and result is not None
    assert (result.stored, result.failed) == (4, 0)
    assert attempts == 2  # a fresh session after the drop
    # the two stored before the drop are not asked again; the dropped one is
    assert scorer.asked == [IDS[0], IDS[1], IDS[2], IDS[2], IDS[3]]
    assert any(line.startswith("connection lost (ConnectionResetError)") for line in lines)
    cost = _cost_line(lines)
    assert "status=complete" in cost
    assert "requests=4 input_tokens=1600 output_tokens=800" in cost


async def test_an_interrupted_run_still_writes_its_cost_line(films: AsyncSession) -> None:
    scorer = FakeScorer({IDS[2]: RuntimeError("a bug, not a connection")})
    result, error, lines, _ = await _run_sync(films, scorer)

    assert result is None and isinstance(error, RuntimeError)
    assert "stored 2, failed 0" in lines
    cost = _cost_line(lines)
    assert "status=interrupted" in cost
    assert "requests=2 input_tokens=800 output_tokens=400" in cost  # what was spent


async def test_a_connection_that_never_comes_back_is_interrupted(films: AsyncSession) -> None:
    down = ConnectionResetError("network down")
    scorer = FakeScorer({IDS[1]: [down, down, down, down]})
    _, error, lines, attempts = await _run_sync(films, scorer, reconnect_delays=(1.0, 1.0))

    assert isinstance(error, ConnectionResetError)
    assert attempts == 3  # first try + 2 reconnects
    cost = _cost_line(lines)
    assert "status=interrupted" in cost and "requests=1 " in cost
    assert await films.get(MovieTraits, IDS[0]) is not None  # kept


async def test_an_account_refusal_is_reported_as_stopped(films: AsyncSession) -> None:
    scorer = FakeScorer({IDS[1]: ProviderUnavailable("400 FAILED_PRECONDITION")})
    result, error, lines, _ = await _run_sync(films, scorer)

    assert error is None and result is not None and result.stopped
    assert "status=stopped" in _cost_line(lines)
