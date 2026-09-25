"""Catalogue ingestion: TMDB -> movies, genres, keywords, people, credits.

    python -m app.pipelines.ingest               # plan (or resume) and ingest
    python -m app.pipelines.ingest --plan-only   # show the catalogue it would pick

Resumable: the plan (an ordered id list) and a cursor live in `sync_runs`. A run that
dies at film 3,000 continues from 3,000 on the next invocation. A dropped database
connection is retried automatically (RECONNECT_ATTEMPTS); data errors are not. Upserts
make re-running safe. TMDB is free but rate-limited, so requests are spaced
(settings.tmdb_*).
"""

import argparse
import asyncio
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import (
    Credit,
    Genre,
    Keyword,
    Movie,
    MovieGenre,
    MovieKeyword,
    Person,
    SyncRun,
)
from app.pipelines.catalogue import Selection, build_pools, select_catalogue
from app.pipelines.db import job_session
from app.pipelines.tmdb import FilmRecord, TmdbClient, TmdbNotFound, to_film_record

KIND = "catalogue"
CHUNK = 25  # films fetched concurrently and committed together
RECONNECT_ATTEMPTS = 5
RECONNECT_DELAYS = (5.0, 15.0, 30.0, 60.0, 120.0)


class IngestStore(Protocol):
    async def open_run(self) -> SyncRun | None: ...
    async def create_run(self, planned_ids: list[int]) -> SyncRun: ...
    async def upsert_films(self, records: Sequence[FilmRecord]) -> None: ...
    async def save_progress(self, run: SyncRun) -> None: ...
    async def rollback(self) -> None: ...


def pending_ids(run: SyncRun) -> list[int]:
    """The part of the plan not yet processed."""
    return [int(i) for i in run.planned_ids[run.cursor :]]


class IngestJob:
    def __init__(
        self,
        store: IngestStore,
        client: TmdbClient,
        *,
        concurrency: int,
        log: Callable[[str], None] = print,
    ) -> None:
        self._store = store
        self._client = client
        self._semaphore = asyncio.Semaphore(concurrency)
        self._log = log

    async def start_or_resume(self, plan: Callable[[], Awaitable[list[int]]]) -> SyncRun:
        """Resume the open run if there is one; otherwise plan a new one."""
        run = await self._store.open_run()
        if run is not None:
            self._log(f"resuming run {run.id} at {run.cursor}/{len(run.planned_ids)}")
            return run
        planned = await plan()
        run = await self._store.create_run(planned)
        self._log(f"started run {run.id}: {len(planned)} films planned")
        return run

    async def run(self, run: SyncRun) -> SyncRun:
        todo = pending_ids(run)
        try:
            for start in range(0, len(todo), CHUNK):
                chunk = todo[start : start + CHUNK]
                results = await asyncio.gather(*(self._fetch(i) for i in chunk))
                records = [r for r in results if r is not None]
                # One write per chunk, committed together with the cursor that covers it.
                await self._store.upsert_films(records)
                run.processed_count += len(records)
                run.skipped_count += len(chunk) - len(records)
                run.last_processed_id = chunk[-1]
                run.cursor += len(chunk)
                await self._store.save_progress(run)
                if run.cursor % 250 < CHUNK or run.cursor == len(run.planned_ids):
                    self._log(f"  {run.cursor}/{len(run.planned_ids)}")
        except Exception as exc:
            # A failed statement aborts the transaction; clear it so the failure itself
            # can be recorded. The cursor still points at the last committed chunk.
            try:
                await self._store.rollback()
                run.status = "failed"
                run.error = f"{type(exc).__name__}: {exc}"[:2000]
                await self._store.save_progress(run)
            except Exception as record_exc:  # e.g. the connection itself is gone
                self._log(f"could not record the failure: {type(record_exc).__name__}")
            raise
        run.status = "finished"
        run.finished_at = datetime.now(UTC)
        run.error = None
        await self._store.save_progress(run)
        return run

    async def _fetch(self, movie_id: int) -> FilmRecord | None:
        async with self._semaphore:
            try:
                payload = await self._client.movie(movie_id)
            except TmdbNotFound:
                return None
        return to_film_record(payload)


class SqlIngestStore:
    """IngestStore on PostgreSQL. Every write is an upsert, so re-runs are safe."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def open_run(self) -> SyncRun | None:
        stmt = (
            select(SyncRun)
            .where(SyncRun.kind == KIND, SyncRun.status.in_(("running", "failed")))
            .order_by(SyncRun.id.desc())
            .limit(1)
        )
        run = (await self._session.execute(stmt)).scalar_one_or_none()
        if run is not None and run.status == "failed":
            run.status = "running"
            run.error = None
        return run

    async def create_run(self, planned_ids: list[int]) -> SyncRun:
        run = SyncRun(
            kind=KIND,
            status="running",
            planned_ids=planned_ids,
            cursor=0,
            processed_count=0,
            skipped_count=0,
        )
        self._session.add(run)
        await self._session.commit()
        return run

    async def save_progress(self, run: SyncRun) -> None:
        self._session.add(run)
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def upsert_film(self, record: FilmRecord) -> None:
        await self.upsert_films([record])

    async def upsert_films(self, records: Sequence[FilmRecord]) -> None:
        """Upsert a chunk of films with one statement per table.

        The database is a network round trip away (~170 ms to Supabase from here), so the
        statement count per chunk, not per film, is what sets the ingestion time.
        """
        if not records:
            return
        s = self._session
        now = datetime.now(UTC)
        by_id = {r.movie["id"]: r for r in records}  # a repeated id keeps its last payload
        movie_ids = list(by_id)
        movies = [{**r.movie, "synced_at": now} for r in by_id.values()]

        stmt = insert(Movie).values(movies)
        await s.execute(
            stmt.on_conflict_do_update(
                index_elements=[Movie.id],
                set_={k: stmt.excluded[k] for k in movies[0] if k != "id"},
            )
        )
        await _upsert_named(s, Genre, [g for r in by_id.values() for g in r.genres])
        await _upsert_named(s, Keyword, [k for r in by_id.values() for k in r.keywords])
        people = {p["id"]: p for r in by_id.values() for p in r.people}
        if people:
            stmt = insert(Person).values(list(people.values()))
            await s.execute(
                stmt.on_conflict_do_update(
                    index_elements=[Person.id],
                    set_={"name": stmt.excluded.name, "profile_path": stmt.excluded.profile_path},
                )
            )

        # Link tables and credits are replaced wholesale: the newest payload is the truth.
        await s.execute(delete(MovieGenre).where(MovieGenre.movie_id.in_(movie_ids)))
        await s.execute(delete(MovieKeyword).where(MovieKeyword.movie_id.in_(movie_ids)))
        await s.execute(delete(Credit).where(Credit.movie_id.in_(movie_ids)))
        genre_links = [
            {"movie_id": m, "genre_id": g} for m, r in by_id.items() for g, _ in r.genres
        ]
        if genre_links:
            await s.execute(insert(MovieGenre).values(genre_links).on_conflict_do_nothing())
        keyword_links = [
            {"movie_id": m, "keyword_id": k} for m, r in by_id.items() for k, _ in r.keywords
        ]
        if keyword_links:
            await s.execute(insert(MovieKeyword).values(keyword_links).on_conflict_do_nothing())
        credits = [c for r in by_id.values() for c in r.credits]
        if credits:
            await s.execute(insert(Credit).values(credits))


async def _upsert_named(
    session: AsyncSession, model: type[Genre] | type[Keyword], rows: Sequence[tuple[int, str]]
) -> None:
    if not rows:
        return
    unique = {row_id: name for row_id, name in rows}
    stmt = insert(model).values([{"id": i, "name": n} for i, n in unique.items()])
    await session.execute(
        stmt.on_conflict_do_update(index_elements=["id"], set_={"name": stmt.excluded.name})
    )


def describe(selection: Selection) -> str:
    decades = ", ".join(f"{d}s: {n}" for d, n in sorted(selection.by_decade.items()))
    top = list(selection.by_language.items())[:10]
    languages = ", ".join(f"{lang}: {n}" for lang, n in top)
    return (
        f"{len(selection.ids)} films\n"
        f"  by decade:   {decades}\n"
        f"  by language: {languages} ({len(selection.by_language)} languages in total)"
    )


# asyncpg error classes that mean "try again later", not "this data is wrong".
TRANSIENT_DB_ERRORS = (
    "ConnectionDoesNotExistError",  # the connection dropped
    "LockNotAvailableError",  # lock_timeout: another session holds the rows
    "QueryCanceledError",  # statement_timeout, usually for the same reason
)


def is_connection_loss(exc: BaseException) -> bool:
    """A dropped connection or a lock wait (retry later), not a data error (don't)."""
    if isinstance(exc, DBAPIError):
        if exc.connection_invalidated:
            return True
        return type(exc.orig).__name__ in TRANSIENT_DB_ERRORS or isinstance(exc.orig, OSError)
    return isinstance(exc, OSError | TimeoutError)


async def with_reconnect(
    attempt: Callable[[], Awaitable[None]],
    *,
    delays: Sequence[float] = RECONNECT_DELAYS,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    log: Callable[[str], None] = print,
) -> None:
    """Run `attempt`, re-running it after a lost connection. It must resume, not restart."""
    for number in range(len(delays) + 1):
        try:
            await attempt()
            return
        except Exception as exc:
            if not is_connection_loss(exc) or number == len(delays):
                raise
            log(f"connection lost ({type(exc).__name__}); resuming in {delays[number]:.0f}s")
            await sleep(delays[number])


async def _plan(client: TmdbClient, target: int) -> Selection:
    settings = get_settings()
    pools = await build_pools(client, target, settings.catalogue_min_votes)
    return select_catalogue(pools, target, settings.catalogue_max_language_share)


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--plan-only", action="store_true", help="print the plan, ingest nothing")
    parser.add_argument("--target", type=int, help="override settings.catalogue_target")
    args = parser.parse_args(argv)
    settings = get_settings()
    target = args.target or settings.catalogue_target

    async with TmdbClient() as client:
        if args.plan_only:
            print(describe(await _plan(client, target)))
            return

        async def plan() -> list[int]:
            selection = await _plan(client, target)
            print(describe(selection))
            return selection.ids

        async def attempt() -> None:
            # A fresh connection each attempt; start_or_resume finds the open run.
            async with job_session() as session:
                store = SqlIngestStore(session)
                job = IngestJob(store, client, concurrency=settings.tmdb_concurrency)
                run = await job.run(await job.start_or_resume(plan))
                print(
                    f"run {run.id} {run.status}: {run.processed_count} ingested, "
                    f"{run.skipped_count} skipped (gone from TMDB)"
                )

        await with_reconnect(attempt)


if __name__ == "__main__":
    asyncio.run(main())
