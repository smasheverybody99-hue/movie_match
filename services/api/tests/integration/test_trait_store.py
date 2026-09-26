"""Trait batches end to end, with a fake Gemini client. No real API call anywhere.

Batch results come from tests/fixtures/gemini_batch_results.json, parsed through the SDK's
own InlinedResponse, and requests are checked against its InlinedRequest, so a payload in
the wrong shape fails loudly.
"""

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MovieTraits, TraitBatch, TraitFailure
from app.pipelines.ingest import SqlIngestStore
from app.pipelines.tmdb import to_film_record
from app.pipelines.traits import (
    MAX_ATTEMPTS,
    MODEL,
    BatchNotReady,
    build_prompt,
    collect,
    load_films,
    select_pending,
    submit,
)
from app.traits import SPEC_VERSION, TRAIT_KEYS
from tests.conftest import load_fixture

IDS = [550, 13, 680, 155]
RESULTS = "gemini_batch_results.json"


class FakeBatches:
    """`client.batches`: create() records what was sent, get() serves the job's results."""

    def __init__(self, results: list[dict], state: str = "JOB_STATE_SUCCEEDED") -> None:
        self._results = results
        self._state = state
        self.created: list[dict[str, Any]] = []

    async def create(self, *, model: str, src: list[dict], config: dict) -> types.BatchJob:
        for request in src:
            types.InlinedRequest.model_validate(request)  # the SDK's own shape check
        self.created.append({"model": model, "src": src, "config": config})
        return types.BatchJob(name=f"batches/fake{uuid.uuid4().hex}")  # unique, like real names

    async def get(self, *, name: str) -> types.BatchJob:
        job: dict[str, Any] = {"name": name, "state": self._state}
        if self._state in ("JOB_STATE_SUCCEEDED", "JOB_STATE_PARTIALLY_SUCCEEDED"):
            job["dest"] = {"inlinedResponses": self._results}
        return types.BatchJob.model_validate(job)


def _client(results: list[dict] | None = None, state: str = "JOB_STATE_SUCCEEDED") -> Any:
    return SimpleNamespace(
        batches=FakeBatches(results if results is not None else load_fixture(RESULTS), state)
    )


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

    sent = client.batches.created[0]
    assert sent["model"] == MODEL
    assert [r["metadata"]["key"] for r in sent["src"]] == ["movie-550", "movie-13"]
    batch = await films.get(TraitBatch, batch_id)
    assert batch is not None
    assert batch.id.startswith("batches/")
    assert batch.movie_ids == [550, 13]
    assert batch.model == MODEL
    assert batch.status == "submitted"


async def test_collect_stores_valid_and_records_the_rest(films: AsyncSession) -> None:
    client = _client()
    batch_id = await submit(films, client, await load_films(films, IDS))
    outcome = await collect(films, client, batch_id)

    assert (outcome.stored, outcome.failed, outcome.state) == (1, 3, "collected")

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
    assert failures[155].last_error.startswith("batch result errored: The model is overloaded")
    assert all(f.attempts == 1 for f in failures.values())

    # Malformed films get NO trait row - never one filled with defaults.
    for movie_id in (13, 680, 155):
        assert await films.get(MovieTraits, movie_id) is None

    batch = await films.get(TraitBatch, batch_id)
    assert batch is not None and batch.status == "collected" and batch.collected_at is not None


async def test_collect_measures_tokens_thinking_included(films: AsyncSession) -> None:
    client = _client()
    outcome = await collect(
        films, client, await submit(films, client, await load_films(films, IDS))
    )
    # prompt 412 + 398 + 405; output 231 + 41 + (2000 + 48 thinking); the errored item has none
    assert outcome.input_tokens == 1215
    assert outcome.output_tokens == 2320


async def test_running_batch_is_not_collected(films: AsyncSession) -> None:
    client = _client(state="JOB_STATE_RUNNING")
    batch_id = await submit(films, client, await load_films(films, IDS))
    with pytest.raises(BatchNotReady, match="JOB_STATE_RUNNING"):
        await collect(films, client, batch_id)

    batch = await films.get(TraitBatch, batch_id)
    assert batch is not None and batch.status == "submitted"
    assert await films.get(TraitFailure, 13) is None


@pytest.mark.parametrize(
    ("job_state", "status"),
    [
        ("JOB_STATE_FAILED", "failed"),
        ("JOB_STATE_CANCELLED", "cancelled"),
        ("JOB_STATE_EXPIRED", "expired"),
    ],
)
async def test_dead_batch_leaves_its_films_pending(
    films: AsyncSession, job_state: str, status: str
) -> None:
    client = _client(state=job_state)
    batch_id = await submit(films, client, await load_films(films, IDS))
    outcome = await collect(films, client, batch_id)

    assert (outcome.state, outcome.stored, outcome.failed) == (status, 0, 0)
    batch = await films.get(TraitBatch, batch_id)
    assert batch is not None and batch.status == status
    # A job that never produced results is not the film's fault: no attempt is counted.
    assert await films.get(TraitFailure, 13) is None
    assert {550, 13, 680, 155} <= set(await select_pending(films, limit=100))


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

    fixed = load_fixture(RESULTS)[0]
    fixed["metadata"]["key"] = "movie-13"
    retry = _client([fixed])
    await collect(films, retry, await submit(films, retry, await load_films(films, [13])))
    assert await films.get(MovieTraits, 13) is not None
    assert await films.get(TraitFailure, 13, populate_existing=True) is None


async def test_pending_excludes_scored_films_and_orders_by_popularity(films: AsyncSession) -> None:
    client = _client([load_fixture(RESULTS)[0]])
    await collect(films, client, await submit(films, client, await load_films(films, [550])))

    pending = [i for i in await select_pending(films, limit=100) if i in IDS]
    assert 550 not in pending
    assert pending == [680, 155, 13]  # popularity 50, 45, 40


async def test_pending_respects_limit(films: AsyncSession) -> None:
    assert len(await select_pending(films, limit=2)) == 2


async def test_pending_by_hand_picked_ids_keeps_the_list_order(films: AsyncSession) -> None:
    client = _client([load_fixture(RESULTS)[0]])
    await collect(films, client, await submit(films, client, await load_films(films, [550])))

    # 550 is scored and 999_999_999 is not in the catalogue: both are skipped.
    assert await select_pending(films, 10, [155, 550, 999_999_999, 13]) == [155, 13]
    assert await select_pending(films, 1, [155, 13]) == [155]
