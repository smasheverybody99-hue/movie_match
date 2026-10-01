"""Trait extraction: movie -> 14-dimension Movie DNA vector.

    python -m app.pipelines.traits submit --limit 50 --dry-run   # prompt + cost, no API call
    python -m app.pipelines.traits submit --limit 50 --yes       # real, paid batch
    python -m app.pipelines.traits submit --ids ../../docs/review-films.md --dry-run
    python -m app.pipelines.traits collect <batch_id>
    python -m app.pipelines.traits status

Runs as a batch job, never inside a request, through the configured provider's batch API
(`LLM_PROVIDER`, ADR 0006), which halves the token cost. Nothing here knows the vendor: the
prompt, the JSON contract, parsing, storage and attempt counting are ours; the provider
only carries requests and answers (app/providers/). Runs are staged (CLAUDE.md): 50
films, check by hand, then 500, then the rest - `--limit` has no default so every run
states its size. `--ids` takes a hand-picked list instead (ids, or a file such as
docs/review-films.md).

With `TRAIT_MODE=sync` the same `submit` sends one film per request on the standard API
instead (ADR 0006, amendment 2026-09-30): paced, retried on 429, each film committed as it
arrives, so a stopped run resumes when run again. There is nothing to `collect`.
"""

import argparse
import asyncio
import json
import math
from collections.abc import Awaitable, Callable, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import (
    Credit,
    Genre,
    Keyword,
    Movie,
    MovieGenre,
    MovieKeyword,
    MovieTraits,
    Person,
    TraitBatch,
    TraitFailure,
)
from app.pipelines.cli import read_ids, utf8_console
from app.pipelines.db import job_session
from app.pipelines.ingest import RECONNECT_DELAYS, with_reconnect
from app.providers import get_provider
from app.providers import usage as cost_log
from app.providers.base import (
    Pricing,
    ProviderUnavailable,
    RateLimited,
    TraitExtractor,
    TraitRequest,
    TraitScorer,
    TransientError,
    Usage,
)
from app.traits import SPEC_VERSION, TRAIT_KEYS, to_vector

MAX_ATTEMPTS = 2  # first try + one retry, then the film is recorded as failed

# Estimation constants until a staged run measures the real numbers.
CHARS_PER_TOKEN = 3.5  # conservative for English prose; real tokenisation is usually denser
EXPECTED_OUTPUT_TOKENS = 250  # 14 integers + a two-sentence summary, as JSON

SYSTEM_PROMPT = f"""You score films on fixed dimensions for a recommendation engine.

Return ONLY a JSON object with exactly these keys, each an integer 0-100:
{", ".join(TRAIT_KEYS)}

Plus one key "summary": two sentences, plain language, describing what kind of viewer
this film is for. No markdown, no commentary outside the JSON.

Scoring guidance:
- 50 means "average for a feature film", not "unknown". Use the full range.
- pacing: 0 contemplative, 100 relentless.
- realism: 0 fully fantastical, 100 grounded.
- darkness: 0 light and warm, 100 bleak.
- ending_ambiguity: 0 fully resolved, 100 deliberately unresolved.
- Score what the film IS, not how good it is. Quality is not a dimension."""

# The same contract as the prompt, enforced by the API. parse_response still validates.
RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **{key: {"type": "integer", "minimum": 0, "maximum": 100} for key in TRAIT_KEYS},
        "summary": {"type": "string"},
    },
    "required": [*TRAIT_KEYS, "summary"],
}


def build_prompt(movie: dict[str, Any]) -> str:
    """One film -> the user message for the batch request."""
    parts = [
        f"Title: {movie['title']}",
        f"Year: {movie.get('year') or 'unknown'}",
        f"Runtime: {movie.get('runtime_minutes') or 'unknown'} minutes",
        f"Genres: {', '.join(movie.get('genres') or []) or 'unknown'}",
        f"Keywords: {', '.join(movie.get('keywords') or []) or 'none'}",
        f"Director: {movie.get('director') or 'unknown'}",
        f"Overview: {movie.get('overview') or 'none'}",
    ]
    return "\n".join(parts)


def parse_response(text: str) -> dict[str, Any]:
    """Model output -> validated scores. Raises ValueError on anything malformed.

    Extra keys are ignored. A ```json fence around the object is tolerated; anything
    else that is not a single JSON object is rejected.
    """
    body = text.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
        body = body.rsplit("```", 1)[0]
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")

    scores: dict[str, float] = {}
    for key in TRAIT_KEYS:
        if key not in data:
            raise ValueError(f"missing trait: {key}")
        value = data[key]
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"{key} is not a number: {value!r}")
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(f"{key} out of range: {value}")
        scores[key] = float(value)
    return {"scores": scores, "summary": str(data.get("summary") or "").strip() or None}


def custom_id(movie_id: int) -> str:
    return f"movie-{movie_id}"


def movie_id_from(custom: str) -> int:
    prefix, _, value = custom.partition("-")
    if prefix != "movie" or not value.isdigit():
        raise ValueError(f"unexpected custom_id: {custom}")
    return int(value)


def build_request(film: dict[str, Any]) -> TraitRequest:
    """One film -> one provider-neutral request. `key` is how its answer finds the film."""
    return TraitRequest(
        key=custom_id(film["id"]),
        system=SYSTEM_PROMPT,
        prompt=build_prompt(film),
        schema=RESPONSE_SCHEMA,
    )


@dataclass(frozen=True)
class CostEstimate:
    films: int
    input_tokens: int
    output_tokens: int
    pricing: Pricing

    @property
    def usd(self) -> float:
        return self.pricing.usd(Usage(0, self.input_tokens, self.output_tokens))

    def scaled_to(self, films: int) -> "CostEstimate":
        """Same per-film averages, different film count."""
        if self.films == 0:
            return CostEstimate(films, 0, 0, self.pricing)
        ratio = films / self.films
        return CostEstimate(
            films,
            round(self.input_tokens * ratio),
            round(self.output_tokens * ratio),
            self.pricing,
        )


def estimate_cost(films: Sequence[dict[str, Any]], pricing: Pricing) -> CostEstimate:
    """Approximate batch cost from prompt length, at `pricing`. No API call."""
    per_request_overhead = len(SYSTEM_PROMPT) + 20  # system prompt + message framing
    chars = sum(per_request_overhead + len(build_prompt(f)) for f in films)
    return CostEstimate(
        films=len(films),
        input_tokens=math.ceil(chars / CHARS_PER_TOKEN),
        output_tokens=EXPECTED_OUTPUT_TOKENS * len(films),
        pricing=pricing,
    )


# --- database side ----------------------------------------------------------------


async def select_pending(
    session: AsyncSession, limit: int, ids: Sequence[int] | None = None
) -> list[int]:
    """Films with no trait vector that have not exhausted their attempts.

    Most popular first; or, given `ids`, those of them still pending, in the given order.
    """
    stmt = (
        select(Movie.id)
        .outerjoin(MovieTraits, MovieTraits.movie_id == Movie.id)
        .outerjoin(TraitFailure, TraitFailure.movie_id == Movie.id)
        .where(MovieTraits.movie_id.is_(None))
        .where((TraitFailure.movie_id.is_(None)) | (TraitFailure.attempts < MAX_ATTEMPTS))
    )
    if ids is not None:
        pending = set((await session.execute(stmt.where(Movie.id.in_(ids)))).scalars().all())
        return [i for i in ids if i in pending][:limit]
    stmt = stmt.order_by(Movie.popularity.desc().nullslast(), Movie.id).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def load_films(session: AsyncSession, ids: Sequence[int]) -> list[dict[str, Any]]:
    """Films as prompt inputs: title, year, runtime, genres, keywords, director, overview."""
    if not ids:
        return []
    movies = (await session.execute(select(Movie).where(Movie.id.in_(ids)))).scalars().all()
    genres = await _names_by_movie(
        session,
        select(MovieGenre.movie_id, Genre.name)
        .join(Genre, Genre.id == MovieGenre.genre_id)
        .where(MovieGenre.movie_id.in_(ids))
        .order_by(MovieGenre.movie_id, Genre.name),
    )
    keywords = await _names_by_movie(
        session,
        select(MovieKeyword.movie_id, Keyword.name)
        .join(Keyword, Keyword.id == MovieKeyword.keyword_id)
        .where(MovieKeyword.movie_id.in_(ids))
        .order_by(MovieKeyword.movie_id, Keyword.name),
    )
    directors = await _names_by_movie(
        session,
        select(Credit.movie_id, Person.name)
        .join(Person, Person.id == Credit.person_id)
        .where(Credit.movie_id.in_(ids), Credit.job == "Director")
        .order_by(Credit.movie_id, Person.name),
    )
    by_id = {
        m.id: {
            "id": m.id,
            "title": m.title,
            "year": m.release_date.year if m.release_date else None,
            "runtime_minutes": m.runtime_minutes,
            "overview": m.overview,
            "genres": genres.get(m.id, []),
            "keywords": keywords.get(m.id, []),
            "director": ", ".join(directors.get(m.id, [])) or None,
        }
        for m in movies
    }
    return [by_id[i] for i in ids if i in by_id]


async def _names_by_movie(session: AsyncSession, stmt: Any) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for movie_id, name in (await session.execute(stmt)).all():
        out.setdefault(movie_id, []).append(name)
    return out


async def store_traits(
    session: AsyncSession, movie_id: int, parsed: dict[str, Any], model: str
) -> None:
    scores = parsed["scores"]
    values = {
        "movie_id": movie_id,
        "scores": scores,
        "vector": to_vector(scores),
        "summary": parsed["summary"],
        "model": model,
        "spec_version": SPEC_VERSION,
    }
    stmt = insert(MovieTraits).values(**values)
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[MovieTraits.movie_id],
            set_={k: stmt.excluded[k] for k in values if k != "movie_id"},
        )
    )
    await session.execute(delete(TraitFailure).where(TraitFailure.movie_id == movie_id))


async def record_failure(
    session: AsyncSession, movie_id: int, error: str, final: bool = False
) -> None:
    """Count one failed attempt; a `final` failure uses up all of them at once, so the
    film is given up (select_pending leaves it out) instead of being asked again."""
    attempts = MAX_ATTEMPTS if final else 1
    stmt = insert(TraitFailure).values(
        movie_id=movie_id, attempts=attempts, last_error=error[:2000]
    )
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[TraitFailure.movie_id],
            set_={
                "attempts": MAX_ATTEMPTS if final else TraitFailure.attempts + 1,
                "last_error": stmt.excluded.last_error,
                "updated_at": func.now(),
            },
        )
    )


# --- the provider side -------------------------------------------------------------


class BatchNotReady(Exception):
    """The batch job has not reached a final state yet."""


async def submit(session: AsyncSession, extractor: TraitExtractor, films: Sequence[dict]) -> str:
    job_id = await extractor.submit([build_request(f) for f in films])
    session.add(
        TraitBatch(
            id=job_id,
            movie_ids=[f["id"] for f in films],
            model=extractor.model,
            status="submitted",
        )
    )
    await session.commit()
    return job_id


@dataclass
class CollectResult:
    stored: int = 0
    failed: int = 0
    usage: Usage = field(default_factory=Usage)  # output includes thinking tokens
    state: str = "collected"  # or failed / cancelled / expired: the job produced no results

    @property
    def input_tokens(self) -> int:
        return self.usage.input_tokens

    @property
    def output_tokens(self) -> int:
        return self.usage.output_tokens


async def collect(session: AsyncSession, extractor: TraitExtractor, batch_id: str) -> CollectResult:
    """Store every valid result; count every malformed or errored one as an attempt.

    Raises BatchNotReady while the job is still running. A job that ended without results
    (failed, cancelled, expired) is recorded as such and its films stay pending, uncounted.
    """
    result = await extractor.collect(batch_id)
    outcome = CollectResult()
    batch = await session.get(TraitBatch, batch_id)
    if result.state == "running":
        raise BatchNotReady(f"batch {batch_id} is {result.detail}")
    if result.state != "done":
        outcome.state = result.state
        if batch is not None:
            batch.status = outcome.state
            await session.commit()
        return outcome

    model = batch.model if batch is not None else extractor.model
    for answer in result.answers:
        movie_id = movie_id_from(answer.key)
        outcome.usage = outcome.usage + answer.usage
        error = answer.error
        if answer.text is not None:
            try:
                await store_traits(session, movie_id, parse_response(answer.text), model)
                outcome.stored += 1
                continue
            except ValueError as exc:
                error = f"malformed: {exc}"
        await record_failure(session, movie_id, error or "no result", final=answer.final)
        outcome.failed += 1

    if batch is not None:
        batch.status = "collected"
        batch.collected_at = datetime.now(UTC)
    await session.commit()
    return outcome


# --- sync mode: one film per request --------------------------------------------------

MAX_BACKOFF_SECONDS = 120.0

Sleep = Callable[[float], Awaitable[None]]


async def call_with_retries[T](
    call: Callable[[], Awaitable[T]], *, retries: int, base_delay: float, sleep: Sleep
) -> T:
    """`call()`, retried on RateLimited and TransientError up to `retries` more times.

    Waits the provider's own retry hint when it gives one, else base_delay doubling each
    time, never more than MAX_BACKOFF_SECONDS. The last failure is raised as it came.
    """
    attempt = 0
    while True:
        try:
            return await call()
        except (RateLimited, TransientError) as exc:
            if attempt >= retries:
                raise
            hint = exc.retry_after if isinstance(exc, RateLimited) else None
            await sleep(min(hint or base_delay * 2**attempt, MAX_BACKOFF_SECONDS))
            attempt += 1


@dataclass
class SyncResult:
    stored: int = 0
    failed: int = 0
    usage: Usage = field(default_factory=Usage)
    stopped: str | None = None  # why the run ended before the last film; they stay pending


async def score_sync(
    session: AsyncSession,
    scorer: TraitScorer,
    films: Sequence[dict[str, Any]],
    *,
    requests_per_minute: float,
    retries: int,
    sleep: Sleep = asyncio.sleep,
    outcome: SyncResult | None = None,
) -> SyncResult:
    """Score films one request at a time, committing each result as it arrives.

    Counts go into `outcome` as they happen (a new one if none is given), so a caller
    holding it still knows what was stored and what was spent when an error ends the run.

    Resumable by design: every film is stored (or its failed attempt recorded) and
    committed before the next request, and `select_pending` leaves scored films out, so
    a run stopped by a daily quota continues where it stopped when run again. A film the
    provider rate-limits past its retries is not counted as an attempt: it was never
    answered. An account-level refusal (billing, permission) stops the run at once.
    """
    outcome = outcome if outcome is not None else SyncResult()
    pace = 60.0 / requests_per_minute
    for index, film in enumerate(films):
        if index:
            await sleep(pace)
        request = build_request(film)

        async def one(request: TraitRequest = request) -> Any:
            return await scorer.score(request)

        try:
            answer = await call_with_retries(
                one, retries=retries, base_delay=max(pace, 1.0), sleep=sleep
            )
        except (RateLimited, TransientError) as exc:
            left = len(films) - index
            outcome.stopped = (
                f"{type(exc).__name__} after {retries} retries ({exc}); {left} films left "
                "pending - run the same command again later to continue"
            )
            break
        except ProviderUnavailable as exc:
            outcome.stopped = f"the provider refused the account ({exc}); nothing more sent"
            break

        outcome.usage = outcome.usage + answer.usage
        error = answer.error
        if answer.text is not None:
            try:
                await store_traits(session, film["id"], parse_response(answer.text), scorer.model)
                await session.commit()
                outcome.stored += 1
                continue
            except ValueError as exc:
                error = f"malformed: {exc}"
        await record_failure(session, film["id"], error or "no result", final=answer.final)
        await session.commit()
        outcome.failed += 1
    return outcome


SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]


async def run_sync(
    ids: Sequence[int],
    scorer: TraitScorer,
    *,
    requests_per_minute: float,
    retries: int,
    open_session: SessionFactory = job_session,
    reconnect_delays: Sequence[float] = RECONNECT_DELAYS,
    sleep: Sleep = asyncio.sleep,
    report: Callable[[str], None] = print,
) -> SyncResult:
    """A whole sync run over `ids`: resumes after a lost database connection, and always
    reports what it spent.

    Each attempt opens a fresh session and scores the films of `ids` still pending, so
    after a dropped connection (ingest.with_reconnect, the ingestion's own retry) the run
    continues where it stopped instead of starting over. Counts and tokens accumulate in
    one SyncResult across attempts.

    The cost line is written in `finally`: `status=complete`, `stopped` (a quota or an
    account refusal ended it early) or `interrupted` (an error, including a connection
    that did not come back), always with the tokens used so far.
    """
    total = SyncResult()

    async def attempt() -> None:
        async with open_session() as session:
            pending = await select_pending(session, len(ids), ids)
            films = await load_films(session, pending)
            await score_sync(
                session,
                scorer,
                films,
                requests_per_minute=requests_per_minute,
                retries=retries,
                sleep=sleep,
                outcome=total,
            )

    status = "interrupted"
    try:
        await with_reconnect(attempt, delays=reconnect_delays, sleep=sleep, log=report)
        status = "stopped" if total.stopped else "complete"
        return total
    finally:
        report(f"stored {total.stored}, failed {total.failed}")
        report(
            cost_log.record(
                "traits-sync", scorer.provider, scorer.model, total.usage, scorer.pricing, status
            )
        )


# --- CLI ----------------------------------------------------------------------------


def full_catalogue(ingested: int, target: int) -> int:
    """The films a full run would score: the target, or fewer if fewer are ingested.

    The database can hold more films than `catalogue_target` (5,000 were ingested before
    the target dropped to 500); the estimate is for the target, not for all of them.
    """
    return min(ingested, target)


def _print_estimate(
    worker: TraitExtractor | TraitScorer, mode: str, estimate: CostEstimate, catalogue: int
) -> None:
    p = worker.pricing
    rates = f"${p.input_usd_per_mtok} in / ${p.output_usd_per_mtok} out per MTok"
    print(f"{worker.provider} {worker.model}, {mode} ({rates}; {p.source})")
    for label, e in (("this run", estimate), ("full catalogue", estimate.scaled_to(catalogue))):
        print(
            f"  {label:15} {e.films:>6} films  ~{e.input_tokens:>10,} in  "
            f"~{e.output_tokens:>9,} out  ~${e.usd:,.2f}"
        )
    print("  (approximate: input from prompt length, output assumed; a staged run measures both)")


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trait extraction batches.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_submit = sub.add_parser("submit")
    size = p_submit.add_mutually_exclusive_group(required=True)
    size.add_argument("--limit", type=int, help="the N most popular pending films")
    size.add_argument("--ids", help="TMDB ids, or a file listing them (docs/review-films.md)")
    p_submit.add_argument("--dry-run", action="store_true", help="prompt and cost, no API call")
    p_submit.add_argument("--yes", action="store_true", help="confirm a paid run")
    p_collect = sub.add_parser("collect")
    p_collect.add_argument("batch_id")
    sub.add_parser("status")
    args = parser.parse_args(argv)
    settings = get_settings()
    utf8_console()
    cost_log.configure()
    provider = get_provider(settings)
    extractor = provider.trait_extractor()
    scorer = provider.trait_scorer()
    sync = settings.trait_mode == "sync"

    async with job_session() as session:
        if args.command == "status":
            total = await session.scalar(select(func.count()).select_from(Movie))
            scored = await session.scalar(select(func.count()).select_from(MovieTraits))
            failed = await session.scalar(
                select(func.count())
                .select_from(TraitFailure)
                .where(TraitFailure.attempts >= MAX_ATTEMPTS)
            )
            print(f"{scored}/{total} films scored, {failed} failed")
            return

        if args.command == "submit":
            if args.ids:
                wanted = read_ids(args.ids)
                ids = await select_pending(session, len(wanted), wanted)
                if len(ids) < len(wanted):
                    print(
                        f"{len(wanted) - len(ids)} of {len(wanted)} listed films skipped: "
                        "not in the catalogue, already scored, or out of attempts"
                    )
            else:
                ids = await select_pending(session, args.limit)
            films = await load_films(session, ids)
            ingested = await session.scalar(select(func.count()).select_from(Movie)) or 0
            catalogue = full_catalogue(ingested, settings.catalogue_target)
            worker: TraitExtractor | TraitScorer = scorer if sync else extractor
            mode = "sync, one film per request" if sync else "batch"
            _print_estimate(worker, mode, estimate_cost(films, worker.pricing), catalogue)
            if sync:
                rpm = settings.trait_sync_requests_per_minute
                print(
                    f"  pace {rpm:g} requests/minute: ~{len(films) / rpm:.0f} min for this run. "
                    "On a free tier the price above is not charged; its daily quota may "
                    "stop a long run, which then resumes where it stopped."
                )
            if args.dry_run:
                if films:
                    print("\n--- system prompt ---\n" + SYSTEM_PROMPT)
                    print("\n--- first film ---\n" + build_prompt(films[0]))
                return
            if not args.yes:
                raise SystemExit("paid run: re-run with --yes once the estimate is approved")
            if sync:
                # The run opens its own sessions (one per reconnect); end this one's read
                # transaction so the server's idle-in-transaction timeout cannot reap it.
                await session.rollback()
                run = await run_sync(
                    ids,
                    scorer,
                    requests_per_minute=settings.trait_sync_requests_per_minute,
                    retries=settings.trait_sync_retries,
                )
                if run.stopped:
                    raise SystemExit(f"stopped early: {run.stopped}")
                return
            for start in range(0, len(films), settings.trait_batch_size):
                chunk = films[start : start + settings.trait_batch_size]
                job_id = await submit(session, extractor, chunk)
                print(f"submitted batch {job_id}: {len(chunk)} films")
            return

        try:
            result = await collect(session, extractor, args.batch_id)
        except BatchNotReady as exc:
            raise SystemExit(f"{exc}; try later") from exc
        if result.state != "collected":
            raise SystemExit(
                f"batch {args.batch_id} {result.state}: no results; films stay pending"
            )
        print(f"stored {result.stored}, failed {result.failed}")
        # measured tokens (thinking included) at the extractor's batch rate
        print(
            cost_log.record(
                "traits", extractor.provider, extractor.model, result.usage, extractor.pricing
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
