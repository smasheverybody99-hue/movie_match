"""Embeddings: film -> vector in movie_embeddings, for ANN retrieval.

    python -m app.pipelines.embeddings --limit 50 --dry-run   # text, size and cost, no call
    python -m app.pipelines.embeddings --limit 50 --yes       # real, paid

The configured provider's embedder (`LLM_PROVIDER`, ADR 0006) at `EMBEDDING_DIM`
dimensions. Before anything is embedded - dry run included - the size is checked against
the movie_embeddings column; a mismatch stops the run with the way out in the message.

Embedding text is built from title, year, genres, keywords, overview and the trait
summary, so a film must have traits before it can be embedded.
"""

import argparse
import asyncio
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models import EMBEDDING_DIM, Movie, MovieEmbedding, MovieTraits
from app.pipelines.cli import utf8_console
from app.pipelines.db import job_session
from app.pipelines.traits import load_films
from app.providers import get_provider
from app.providers import usage as cost_log
from app.providers.base import Embedder, Usage
from app.schema_checks import EmbeddingDimMismatch, check_embedding_dim

MAX_KEYWORDS = 30
EMBED_CHUNK = 64
CHARS_PER_TOKEN = 3.5


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


async def select_pending(session: AsyncSession, limit: int) -> list[tuple[int, str | None]]:
    """Films that have traits but no embedding, with their trait summary."""
    stmt = (
        select(Movie.id, MovieTraits.summary)
        .join(MovieTraits, MovieTraits.movie_id == Movie.id)
        .outerjoin(MovieEmbedding, MovieEmbedding.movie_id == Movie.id)
        .where(MovieEmbedding.movie_id.is_(None))
        .order_by(Movie.popularity.desc().nullslast(), Movie.id)
        .limit(limit)
    )
    return [(row[0], row[1]) for row in (await session.execute(stmt)).all()]


async def embed_films(
    session: AsyncSession, embedder: Embedder, pending: Sequence[tuple[int, str | None]]
) -> tuple[int, Usage]:
    """Embed and store; returns (stored, usage). Rejects vectors of the wrong size."""
    if embedder.dim != EMBEDDING_DIM:
        raise ValueError(f"embedder is {embedder.dim}-d, column is {EMBEDDING_DIM}-d")
    summaries = dict(pending)
    films = await load_films(session, [movie_id for movie_id, _ in pending])
    stored = 0
    usage = Usage()
    for start in range(0, len(films), EMBED_CHUNK):
        chunk = films[start : start + EMBED_CHUNK]
        texts = [build_embedding_text(f, summaries.get(f["id"])) for f in chunk]
        embedded = await embedder.embed(texts)
        usage = usage + embedded.usage
        if len(embedded.vectors) != len(chunk):
            raise ValueError(f"asked for {len(chunk)} embeddings, got {len(embedded.vectors)}")
        for film, vector in zip(chunk, embedded.vectors, strict=True):
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
            stored += 1
        await session.commit()
    return stored, usage


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Film embeddings.")
    parser.add_argument("--limit", type=int, required=True, help="films in this run")
    parser.add_argument("--dry-run", action="store_true", help="text, size and cost, no call")
    parser.add_argument("--yes", action="store_true", help="confirm a paid run")
    args = parser.parse_args(argv)
    utf8_console()
    cost_log.configure()
    settings = get_settings()
    embedder = get_embedder(settings)

    async with job_session() as session:
        try:
            await check_embedding_dim(session, settings.embedding_dim)
        except EmbeddingDimMismatch as exc:
            raise SystemExit(str(exc)) from exc
        pending = await select_pending(session, args.limit)
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
                f"at {embedder.dim}-d, ~{estimate.input_tokens:,} tokens, "
                f"~${embedder.pricing.usd(estimate):.4f} ({embedder.pricing.source})"
            )
            if texts:
                print("\n--- first text ---\n" + texts[0])
            return
        if not args.yes:
            raise SystemExit("paid run: re-run with --yes once the --dry-run cost is approved")
        stored, usage = await embed_films(session, embedder, pending)
        print(f"stored {stored} embeddings")
        print(
            cost_log.record(
                "embeddings", embedder.provider, embedder.model, usage, embedder.pricing
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
