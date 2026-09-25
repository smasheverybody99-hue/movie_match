"""Trait batches end to end, with a fake Anthropic client. No real API call anywhere.

Batch results come from tests/fixtures/anthropic_batch_results.json, parsed through the
SDK's own MessageBatchIndividualResponse, so a fixture in the wrong shape fails loudly.
"""

from types import SimpleNamespace

import pytest
from anthropic.types.messages import MessageBatchIndividualResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MovieTraits, TraitBatch, TraitFailure
from app.pipelines.ingest import SqlIngestStore
from app.pipelines.tmdb import to_film_record
from app.pipelines.traits import (
    MAX_ATTEMPTS,
    MODEL,
    build_prompt,
    collect,
    load_films,
    select_pending,
    submit,
)
from app.traits import SPEC_VERSION, TRAIT_KEYS
from tests.conftest import load_fixture

IDS = [550, 13, 680, 155]


class FakeBatches:
    def __init__(self, results: list[dict]) -> None:
        self._results = [MessageBatchIndividualResponse.model_validate(r) for r in results]
        self.created: list[list[dict]] = []

    async def create(self, *, requests: list[dict]) -> SimpleNamespace:
        self.created.append(requests)
        return SimpleNamespace(id=f"msgbatch_fake_{len(self.created)}")

    async def results(self, batch_id: str):
        async def stream():
            for item in self._results:
                yield item

        return stream()


def _client(results: list[dict] | None = None) -> SimpleNamespace:
    batches = FakeBatches(
        results if results is not None else load_fixture("anthropic_batch_results.json")
    )
    return SimpleNamespace(messages=SimpleNamespace(batches=batches))


@pytest.fixture
async def films(db_session: AsyncSession) -> AsyncSession:
    store = SqlIngestStore(db_session)
    await store.upsert_film(to_film_record(load_fixture("tmdb_movie_550.json")))
    for movie_id, popularity in ((13, 40.0), (680, 50.0), (155, 45.0)):
        await store.upsert_film(
            to_film_record({"id": movie_id, "title": f"Film {movie_id}", "popularity": popularity})
        )
    return db_session


async def test_load_films_builds_prompt_inputs(films: AsyncSession) -> None:
    [fight_club] = await load_films(films, [550])
    assert fight_club["title"] == "Fight Club"
    assert fight_club["year"] == 1999
    assert fight_club["genres"] == ["Drama", "Thriller"]
    assert "nihilism" in fight_club["keywords"]
    assert fight_club["director"] == "David Fincher"
    assert "Director: David Fincher" in build_prompt(fight_club)


async def test_load_films_keeps_requested_order(films: AsyncSession) -> None:
    assert [f["id"] for f in await load_films(films, [680, 550, 13])] == [680, 550, 13]
    assert await load_films(films, []) == []


async def test_submit_records_the_batch(films: AsyncSession) -> None:
    client = _client()
    batch_id = await submit(films, client, await load_films(films, [550, 13]))

    sent = client.messages.batches.created[0]
    assert [r["custom_id"] for r in sent] == ["movie-550", "movie-13"]
    batch = await films.get(TraitBatch, batch_id)
    assert batch is not None
    assert batch.movie_ids == [550, 13]
    assert batch.model == MODEL
    assert batch.status == "submitted"


async def test_collect_stores_valid_and_records_the_rest(films: AsyncSession) -> None:
    client = _client()
    batch_id = await submit(films, client, await load_films(films, IDS))
    outcome = await collect(films, client, batch_id)

    assert (outcome.stored, outcome.failed) == (1, 3)

    traits = await films.get(MovieTraits, 550)
    assert traits is not None
    assert traits.scores["plot_twist"] == 95.0
    assert list(traits.vector) == [traits.scores[k] for k in TRAIT_KEYS]
    assert traits.model == MODEL
    assert traits.spec_version == SPEC_VERSION
    assert traits.summary and traits.summary.startswith("For viewers")

    failures = {
        f.movie_id: f
        for f in (await films.execute(select(TraitFailure).where(TraitFailure.movie_id.in_(IDS))))
        .scalars()
        .all()
    }
    assert set(failures) == {13, 680, 155}
    assert failures[13].last_error.startswith("malformed: missing trait")
    assert failures[680].last_error == "truncated at max_tokens"
    assert failures[155].last_error == "batch result errored"
    assert all(f.attempts == 1 for f in failures.values())

    # Malformed films get NO trait row - never one filled with defaults.
    for movie_id in (13, 680, 155):
        assert await films.get(MovieTraits, movie_id) is None

    batch = await films.get(TraitBatch, batch_id)
    assert batch is not None and batch.status == "collected" and batch.collected_at is not None


async def test_failed_film_is_retried_once_then_given_up(films: AsyncSession) -> None:
    client = _client()
    for _ in range(MAX_ATTEMPTS):
        pending = await select_pending(films, limit=10)
        assert 13 in pending
        await collect(films, client, await submit(films, client, await load_films(films, IDS)))

    failure = await films.get(TraitFailure, 13, populate_existing=True)
    assert failure is not None and failure.attempts == MAX_ATTEMPTS
    assert 13 not in await select_pending(films, limit=10)


async def test_success_after_a_failure_clears_the_failure(films: AsyncSession) -> None:
    client = _client()
    await collect(films, client, await submit(films, client, await load_films(films, IDS)))
    assert await films.get(TraitFailure, 13) is not None

    fixed = load_fixture("anthropic_batch_results.json")[0]
    fixed["custom_id"] = "movie-13"
    retry = _client([fixed])
    await collect(films, retry, await submit(films, retry, await load_films(films, [13])))
    assert await films.get(MovieTraits, 13) is not None
    assert await films.get(TraitFailure, 13, populate_existing=True) is None


async def test_pending_excludes_scored_films_and_orders_by_popularity(films: AsyncSession) -> None:
    client = _client([load_fixture("anthropic_batch_results.json")[0]])
    await collect(films, client, await submit(films, client, await load_films(films, [550])))

    pending = [i for i in await select_pending(films, limit=100) if i in IDS]
    assert 550 not in pending
    assert pending == [680, 155, 13]  # popularity 50, 45, 40


async def test_pending_respects_limit(films: AsyncSession) -> None:
    assert len(await select_pending(films, limit=2)) == 2
