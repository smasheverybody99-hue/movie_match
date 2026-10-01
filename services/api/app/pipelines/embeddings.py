"""Embeddings: film -> vector in movie_embeddings, for ANN retrieval.

    python -m app.pipelines.embeddings --ids ../../docs/catalogue-500.md --dry-run
    python -m app.pipelines.embeddings --ids ../../docs/catalogue-500.md --yes   # real
    python -m app.pipelines.embeddings --limit 50 --dry-run   # or the N most popular

The configured provider's embedder (`LLM_PROVIDER`, ADR 0006) at `EMBEDDING_DIM`
dimensions. Before anything is embedded - dry run included - the size is checked against
the movie_embeddings column; a mismatch stops the run with the way out in the message.

Run like sync traits (ADR 0006 amendment, 2026-10-01): one film per request, paced at
`EMBEDDING_REQUESTS_PER_MINUTE`, 429s and server errors waited out up to
`EMBEDDING_RETRIES` times, each film committed as it arrives, a lost database connection
retried with `ingest.with_reconnect`, and one cost line written in `finally` with
`status=` and the tokens counted by the provider (`tokens=reported`).

Embedding text is built from title, year, genres, keywords, overview and the trait
summary, so a film must have traits before it can be embedded.
"""

import argparse
import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models import EMBEDDING_DIM, Movie, MovieEmbedding, MovieTraits
from app.pipelines.cli import read_ids, utf8_console
from app.pipelines.db import job_session
from app.pipelines.ingest import RECONNECT_DELAYS, with_reconnect
from app.pipelines.traits import SessionFactory, Sleep, call_with_retries, load_films
from app.providers import get_provider
from app.providers import usage as cost_log
from app.providers.base import (
    Embedded,
    Embedder,
    ProviderUnavailable,
    RateLimited,
    TransientError,
    Usage,
)
from app.schema_checks import EmbeddingDimMismatch, check_embedding_dim

MAX_KEYWORDS = 30
CHARS_PER_TOKEN = 3.5  # dry-run estimate only; real runs report the provider's count


def get_embedder(settings: Settings | None = None) -> Embedder:
    """The configured provider's embedder at the configured size. No network."""
    settings = settings or get_settings()
    return get_provider(settings).embedder(settings.embedding_dim)


def build_embedding_text(film: dict[str, Any], trait_summary: str | None) -> str:
    """Deterministic: the same film always yields the same text, whatever the input order."""
    year = film.get("year")
    title = f"{film['title']} ({year})" if year else film["title"]
    genres = sorted(set(film.get("genres") or []))
    keywords = sorted(set(film.get("keywords") or []))[:MAX_KEYWORDS]
    lines = [f"Title: {title}"]
    if genres:
        lines.append(f"Genres: {', '.join(genres)}")
    if keywords:
        lines.append(f"Keywords: {', '.join(keywords)}")
    if film.get("overview"):
        lines.append(f"Overview: {' '.join(str(film['overview']).split())}")
    if trait_summary:
        lines.append(f"For viewers: {' '.join(trait_summary.split())}")
    return "\n".join(lines)


async def select_pending(
    session: AsyncSession, limit: int, ids: Sequence[int] | None = None
) -> list[tuple[int, str | None]]:
    """Films that have traits but no embedding, with their trait summary.

    Most popular first; or, given `ids`, those of them still pending, in the given order.
    """
    stmt = (
        select(Movie.id, MovieTraits.summary)
        .join(MovieTraits, MovieTraits.movie_id == Movie.id)
        .outerjoin(MovieEmbedding, MovieEmbedding.movie_id == Movie.id)
        .where(MovieEmbedding.movie_id.is_(None))
    )
    if ids is not None:
        found = {row[0]: row[1] for row in (await session.execute(stmt.where(Movie.id.in_(ids))))}
        return [(i, found[i]) for i in ids if i in found][:limit]
    stmt = stmt.order_by(Movie.popularity.desc().nullslast(), Movie.id).limit(limit)
    return [(row[0], row[1]) for row in (await session.execute(stmt)).all()]


@dataclass
class EmbedResult:
    stored: int = 0
    usage: Usage = field(default_factory=Usage)
    stopped: str | None = None  # why the run ended before the last film; they stay pending


async def embed_films(
    session: AsyncSession,
    embedder: Embedder,
    pending: Sequence[tuple[int, str | None]],
    *,
    requests_per_minute: float,
    retries: int,
    sleep: Sleep = asyncio.sleep,
    outcome: EmbedResult | None = None,
) -> EmbedResult:
    """Embed one film per request, paced; store and commit each vector as it arrives.

    Rejects vectors of the wrong size. A rate limit or server error past its retries, or
    an account refusal, ends the run early with `stopped` set; films not reached stay
    pending. Counts go into `outcome` as they happen, so they survive an exception.
    """
    if embedder.dim != EMBEDDING_DIM:
        raise ValueError(f"embedder is {embedder.dim}-d, column is {EMBEDDING_DIM}-d")
    outcome = outcome if outcome is not None else EmbedResult()
    pace = 60.0 / requests_per_minute
    summaries = dict(pending)
    films = await load_films(session, [movie_id for movie_id, _ in pending])
    for index, film in enumerate(films):
        if index:
            await sleep(pace)
        text = build_embedding_text(film, summaries.get(film["id"]))

        async def one(text: str = text) -> Embedded:
            return await embedder.embed([text])

        try:
            embedded = await call_with_retries(
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

        outcome.usage = outcome.usage + embedded.usage
        if len(embedded.vectors) != 1:
            raise ValueError(f"asked for 1 embedding, got {len(embedded.vectors)}")
        vector = embedded.vectors[0]
        if len(vector) != EMBEDDING_DIM:
            raise ValueError(f"film {film['id']}: {len(vector)}-d vector")
        stmt = insert(MovieEmbedding).values(
            movie_id=film["id"], embedding=vector, model=embedder.model
        )
        await session.execute(
            stmt.on_conflict_do_update(
                index_elements=[MovieEmbedding.movie_id],
                set_={"embedding": stmt.excluded.embedding, "model": stmt.excluded.model},
            )
        )
        await session.commit()
        outcome.stored += 1
    return outcome


async def run_embeddings(
    embedder: Embedder,
    *,
    limit: int,
    ids: Sequence[int] | None,
    requests_per_minute: float,
    retries: int,
    open_session: SessionFactory = job_session,
    reconnect_delays: Sequence[float] = RECONNECT_DELAYS,
    sleep: Sleep = asyncio.sleep,
    report: Callable[[str], None] = print,
) -> EmbedResult:
    """A whole embedding run: resumes after a lost database connection (each attempt
    opens a fresh session and takes the films still pending) and writes its cost line in
    `finally`, with status complete, stopped or interrupted."""
    total = EmbedResult()

    async def attempt() -> None:
        async with open_session() as session:
            pending = await select_pending(session, limit, ids)
            await embed_films(
                session,
                embedder,
                pending,
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
        report(f"stored {total.stored} embeddings")
        report(
            cost_log.record(
                "embeddings",
                embedder.provider,
                embedder.model,
                total.usage,
                embedder.pricing,
                status,
            )
        )


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Film embeddings.")
    size = parser.add_mutually_exclusive_group(required=True)
    size.add_argument("--limit", type=int, help="the N most popular pending films")
    size.add_argument("--ids", help="TMDB ids, or a file listing them (docs/catalogue-500.md)")
    parser.add_argument("--dry-run", action="store_true", help="text, size and cost, no call")
    parser.add_argument("--yes", action="store_true", help="confirm a paid run")
    args = parser.parse_args(argv)
    utf8_console()
    cost_log.configure()
    settings = get_settings()
    embedder = get_embedder(settings)
    ids = read_ids(args.ids) if args.ids else None
    limit = len(ids) if ids is not None else args.limit
    rpm = settings.embedding_requests_per_minute

    async with job_session() as session:
        try:
            await check_embedding_dim(session, settings.embedding_dim)
        except EmbeddingDimMismatch as exc:
            raise SystemExit(str(exc)) from exc
        pending = await select_pending(session, limit, ids)
        if ids is not None and len(pending) < len(ids):
            print(
                f"{len(ids) - len(pending)} of {len(ids)} listed films skipped: "
                "no traits yet, already embedded, or not in the catalogue"
            )
        if args.dry_run:
            films = await load_films(session, [movie_id for movie_id, _ in pending])
            summaries = dict(pending)
            texts = [build_embedding_text(f, summaries.get(f["id"])) for f in films]
            estimate = Usage(
                requests=len(texts),
                input_tokens=round(sum(len(t) for t in texts) / CHARS_PER_TOKEN),
                estimated=True,
            )
            print(
                f"{len(texts)} films ready to embed with {embedder.provider} {embedder.model} "
                f"at {embedder.dim}-d, ~{estimate.input_tokens:,} tokens (characters / "
                f"{CHARS_PER_TOKEN}; the real run counts them), "
                f"~${embedder.pricing.usd(estimate):.4f} ({embedder.pricing.source})"
            )
            print(f"  pace {rpm:g} requests/minute: ~{len(texts) / rpm:.0f} min")
            if texts:
                print("\n--- first text ---\n" + texts[0])
            return
        if not args.yes:
            raise SystemExit("paid run: re-run with --yes once the --dry-run cost is approved")
        # The run opens its own sessions (one per reconnect); end this one's read
        # transaction so the server's idle-in-transaction timeout cannot reap it.
        await session.rollback()

    result = await run_embeddings(
        embedder,
        limit=limit,
        ids=ids,
        requests_per_minute=rpm,
        retries=settings.embedding_retries,
    )
    if result.stopped:
        raise SystemExit(f"stopped early: {result.stopped}")


if __name__ == "__main__":
    asyncio.run(main())
