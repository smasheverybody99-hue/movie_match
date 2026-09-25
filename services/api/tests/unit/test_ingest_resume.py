"""A run resumes from its recorded position, and records progress as it goes."""

import json
from collections.abc import Sequence

import httpx
import pytest

from app.models import SyncRun
from app.pipelines import ingest
from app.pipelines.ingest import IngestJob, pending_ids
from app.pipelines.tmdb import FilmRecord, TmdbClient


class FakeStore:
    """In-memory IngestStore. Records every write so tests can inspect it."""

    def __init__(self, open_run: SyncRun | None = None) -> None:
        self.run = open_run
        self.upserted: list[int] = []
        self.progress: list[int] = []  # cursor at each save
        self.rollbacks = 0

    async def open_run(self) -> SyncRun | None:
        return self.run

    async def create_run(self, planned_ids: list[int]) -> SyncRun:
        self.run = _run(planned_ids, cursor=0, run_id=2)
        return self.run

    async def upsert_films(self, records: Sequence[FilmRecord]) -> None:
        self.upserted.extend(r.movie["id"] for r in records)

    async def save_progress(self, run: SyncRun) -> None:
        self.progress.append(run.cursor)

    async def rollback(self) -> None:
        self.rollbacks += 1


def _run(planned: list[int], cursor: int, run_id: int = 1) -> SyncRun:
    return SyncRun(
        id=run_id,
        kind="catalogue",
        status="running",
        planned_ids=planned,
        cursor=cursor,
        processed_count=cursor,
        skipped_count=0,
    )


def _tmdb(requested: list[int], *, missing: set[int] = frozenset(), fail_on: int | None = None):
    """A TmdbClient over a fake transport that serves /movie/{id}."""

    def handler(request: httpx.Request) -> httpx.Response:
        movie_id = int(request.url.path.rsplit("/", 1)[1])
        requested.append(movie_id)
        if movie_id == fail_on:
            return httpx.Response(400, json={"status_message": "bad request"})
        if movie_id in missing:
            return httpx.Response(404, json={"status_code": 34})
        return httpx.Response(
            200, content=json.dumps({"id": movie_id, "title": f"Film {movie_id}"})
        )

    async def no_sleep(_: float) -> None:
        return None

    return TmdbClient(
        "test-key", transport=httpx.MockTransport(handler), rate_per_second=0, sleep=no_sleep
    )


@pytest.fixture(autouse=True)
def small_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingest, "CHUNK", 2)


def test_pending_ids_starts_at_the_cursor() -> None:
    assert pending_ids(_run([10, 20, 30, 40], cursor=3)) == [40]
    assert pending_ids(_run([10, 20], cursor=2)) == []


async def test_resumes_from_recorded_position() -> None:
    run = _run([1, 2, 3, 4, 5, 6, 7], cursor=4)
    store, requested = FakeStore(open_run=run), []
    job = IngestJob(store, _tmdb(requested), concurrency=2, log=lambda _: None)

    async def plan() -> list[int]:
        raise AssertionError("an open run must be resumed, not re-planned")

    resumed = await job.start_or_resume(plan)
    finished = await job.run(resumed)

    assert sorted(requested) == [5, 6, 7]
    assert store.upserted == [5, 6, 7]
    assert finished.cursor == 7
    assert finished.status == "finished"
    assert finished.finished_at is not None
    assert finished.last_processed_id == 7
    assert finished.processed_count == 7


async def test_plans_a_new_run_when_none_is_open() -> None:
    store, requested = FakeStore(), []
    job = IngestJob(store, _tmdb(requested), concurrency=2, log=lambda _: None)

    async def plan() -> list[int]:
        return [11, 12, 13]

    run = await job.run(await job.start_or_resume(plan))
    assert store.upserted == [11, 12, 13]
    assert run.cursor == 3


async def test_progress_is_saved_after_every_chunk() -> None:
    store, requested = FakeStore(open_run=_run([1, 2, 3, 4, 5], cursor=0)), []
    job = IngestJob(store, _tmdb(requested), concurrency=2, log=lambda _: None)
    await job.run(store.run)
    assert store.progress == [2, 4, 5, 5]  # three chunks, then the finishing save


async def test_films_gone_from_tmdb_are_skipped_not_fatal() -> None:
    store, requested = FakeStore(open_run=_run([1, 2, 3], cursor=0)), []
    job = IngestJob(store, _tmdb(requested, missing={2}), concurrency=2, log=lambda _: None)
    run = await job.run(store.run)
    assert store.upserted == [1, 3]
    assert run.skipped_count == 1
    assert run.status == "finished"


async def test_a_crash_leaves_a_resumable_failed_run() -> None:
    run = _run([1, 2, 3, 4, 5, 6], cursor=0)
    store, requested = FakeStore(open_run=run), []
    job = IngestJob(store, _tmdb(requested, fail_on=4), concurrency=2, log=lambda _: None)

    with pytest.raises(httpx.HTTPStatusError):
        await job.run(run)

    assert run.status == "failed"
    assert "HTTPStatusError" in (run.error or "")
    assert store.rollbacks == 1  # cleared before the failure was recorded
    assert run.cursor == 2  # the chunk holding film 4 was not committed
    assert pending_ids(run) == [3, 4, 5, 6]

    # Second invocation: same run, picks up at the recorded position.
    requested.clear()
    retry = IngestJob(store, _tmdb(requested), concurrency=2, log=lambda _: None)
    await retry.run(run)
    assert sorted(requested) == [3, 4, 5, 6]
    assert run.status == "finished"
    assert run.error is None
