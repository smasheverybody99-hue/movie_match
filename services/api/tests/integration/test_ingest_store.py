"""sync_runs persistence: the SQL side of resumability."""

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SyncRun
from app.pipelines.ingest import KIND, SqlIngestStore


async def _clear_open_runs(session: AsyncSession) -> None:
    """The test database may hold runs from earlier suites; close them for this test."""
    await session.execute(update(SyncRun).where(SyncRun.kind == KIND).values(status="finished"))


async def test_no_open_run_when_none_is_running(db_session: AsyncSession) -> None:
    await _clear_open_runs(db_session)
    assert await SqlIngestStore(db_session).open_run() is None


async def test_created_run_is_found_again_with_its_plan(db_session: AsyncSession) -> None:
    await _clear_open_runs(db_session)
    store = SqlIngestStore(db_session)
    run = await store.create_run([550, 680, 13])
    run.cursor = 2
    run.last_processed_id = 680
    await store.save_progress(run)

    reopened = await store.open_run()
    assert reopened is not None
    assert reopened.id == run.id
    assert reopened.planned_ids == [550, 680, 13]
    assert reopened.cursor == 2
    assert reopened.last_processed_id == 680


async def test_failed_run_is_reopened_as_running(db_session: AsyncSession) -> None:
    await _clear_open_runs(db_session)
    store = SqlIngestStore(db_session)
    run = await store.create_run([1, 2])
    run.status, run.error = "failed", "ConnectError: reset"
    await store.save_progress(run)

    reopened = await store.open_run()
    assert reopened is not None and reopened.id == run.id
    assert reopened.status == "running"
    assert reopened.error is None


async def test_finished_run_is_not_reopened(db_session: AsyncSession) -> None:
    await _clear_open_runs(db_session)
    store = SqlIngestStore(db_session)
    run = await store.create_run([1])
    run.status = "finished"
    await store.save_progress(run)
    assert await store.open_run() is None


async def test_failure_can_be_recorded_after_a_database_error(db_session: AsyncSession) -> None:
    """Reproduces the live failure: a bad row aborts the transaction, the run must still
    be markable as failed afterwards."""
    import pytest
    from sqlalchemy.exc import DBAPIError

    from app.pipelines.tmdb import FilmRecord

    await _clear_open_runs(db_session)
    store = SqlIngestStore(db_session)
    run = await store.create_run([1, 2])
    bad = FilmRecord(
        movie={"id": 8_100_001, "title": "Bad", "original_language": "x" * 50},  # column is 10
    )
    with pytest.raises(DBAPIError):
        await store.upsert_films([bad])

    await store.rollback()
    run.status, run.error = "failed", "StringDataRightTruncationError"
    await store.save_progress(run)

    reopened = await store.open_run()
    assert reopened is not None and reopened.id == run.id
