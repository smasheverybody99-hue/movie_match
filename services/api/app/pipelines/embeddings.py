"""Embeddings: film -> vector in movie_embeddings, for ANN retrieval.

    python -m app.pipelines.embeddings --limit 50 --dry-run   # text + size, no API call

The provider is not chosen yet (see the phase-1 report). Everything here works against
the `Embedder` protocol; wiring a real provider means one class and one setting. Until
then `get_embedder()` refuses, so nothing can call a paid API by accident.

Embedding text is built from title, year, genres, keywords, overview and the trait
summary, so a film must have traits before it can be embedded.
"""

import argparse
import asyncio
from collections.abc import Sequence
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EMBEDDING_DIM, Movie, MovieEmbedding, MovieTraits
from app.pipelines.db import job_session
from app.pipelines.traits import load_films

MAX_KEYWORDS = 30
EMBED_CHUNK = 64
CHARS_PER_TOKEN = 3.5


class Embedder(Protocol):
    model: str
    dim: int

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def get_embedder() -> Embedder:
    raise RuntimeError(
        "No embedding provider is configured yet. Choose one (see the phase-1 report), "
        "implement Embedder for it, and match EMBEDDING_DIM with a migration."
    )


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
) -> int:
    """Embed and store. Rejects vectors of the wrong size instead of storing them."""
    if embedder.dim != EMBEDDING_DIM:
        raise ValueError(f"embedder is {embedder.dim}-d, column is {EMBEDDING_DIM}-d")
    summaries = dict(pending)
    films = await load_films(session, [movie_id for movie_id, _ in pending])
    stored = 0
    for start in range(0, len(films), EMBED_CHUNK):
        chunk = films[start : start + EMBED_CHUNK]
        texts = [build_embedding_text(f, summaries.get(f["id"])) for f in chunk]
        vectors = await embedder.embed(texts)
        if len(vectors) != len(chunk):
            raise ValueError(f"asked for {len(chunk)} embeddings, got {len(vectors)}")
        for film, vector in zip(chunk, vectors, strict=True):
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
    return stored


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Film embeddings.")
    parser.add_argument("--limit", type=int, required=True, help="films in this run")
    parser.add_argument("--dry-run", action="store_true", help="text and size, no API call")
    args = parser.parse_args(argv)

    async with job_session() as session:
        pending = await select_pending(session, args.limit)
        if args.dry_run:
            films = await load_films(session, [movie_id for movie_id, _ in pending])
            summaries = dict(pending)
            texts = [build_embedding_text(f, summaries.get(f["id"])) for f in films]
            tokens = sum(len(t) for t in texts) / CHARS_PER_TOKEN
            print(f"{len(texts)} films ready to embed, ~{tokens:,.0f} tokens in total")
            if texts:
                print("\n--- first text ---\n" + texts[0])
            return
        stored = await embed_films(session, get_embedder(), pending)
        print(f"stored {stored} embeddings")


if __name__ == "__main__":
    asyncio.run(main())
