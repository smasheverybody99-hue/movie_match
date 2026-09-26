"""Embeddings: film -> vector in movie_embeddings, for ANN retrieval.

    python -m app.pipelines.embeddings --limit 50 --dry-run   # text, size and cost, no call
    python -m app.pipelines.embeddings --limit 50             # real, paid

Gemini Embedding 2 on the paid tier (ADR 0004), behind the `Embedder` protocol. It returns
3,072 dimensions by default; we ask for 1,536 (`output_dimensionality`), which fits the
column and pgvector's 2,000-dimension HNSW limit, and the API normalises truncated vectors.

Embedding text is built from title, year, genres, keywords, overview and the trait
summary, so a film must have traits before it can be embedded.
"""

import argparse
import asyncio
from collections.abc import Sequence
from typing import Any, Protocol

from google.genai import errors, types
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Settings, get_settings
from app.models import EMBEDDING_DIM, Movie, MovieEmbedding, MovieTraits
from app.pipelines.cli import utf8_console
from app.pipelines.db import job_session
from app.pipelines.gemini import gemini_client
from app.pipelines.traits import load_films

MAX_KEYWORDS = 30
EMBED_CHUNK = 64
CHARS_PER_TOKEN = 3.5

EMBEDDING_MODEL = "gemini-embedding-2"
# Standard (not batch) paid-tier rate, USD per million tokens, checked 2026-09-26. The Batch
# API is half of this; not worth a second polling loop for ~$0.09 per 5,000 films (ADR 0004).
EMBEDDING_USD_PER_MTOK = 0.20
EMBED_CONCURRENCY = 8
EMBED_ATTEMPTS = 5
_BACKOFF = wait_exponential(multiplier=1, max=30)
_TRANSIENT_CODES = {429, 500, 502, 503, 504}


class Embedder(Protocol):
    model: str
    dim: int

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def _is_transient(exc: BaseException) -> bool:
    return isinstance(exc, errors.APIError) and exc.code in _TRANSIENT_CODES


class GeminiEmbedder:
    """Film text -> 1,536-d vectors through Gemini Embedding 2.

    The model returns ONE aggregated embedding for a request with several inputs, so each
    text is its own request. Requests run a few at a time; rate limits and server errors
    are retried with backoff, anything else stops the run.
    """

    model = EMBEDDING_MODEL
    dim = EMBEDDING_DIM

    def __init__(
        self,
        client: Any,
        *,
        concurrency: int = EMBED_CONCURRENCY,
        wait: Any = _BACKOFF,
    ) -> None:
        self._client = client
        self._concurrency = concurrency
        self._wait = wait

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        gate = asyncio.Semaphore(self._concurrency)

        async def one(text: str) -> list[float]:
            async with gate:
                return await self._embed_one(text)

        async with asyncio.TaskGroup() as group:  # a failure cancels the rest
            tasks = [group.create_task(one(t)) for t in texts]
        return [t.result() for t in tasks]

    async def _embed_one(self, text: str) -> list[float]:
        # Embedding 2 takes no task_type; the documented document format is "title | text".
        content = f"title: none | text: {text}"
        config = types.EmbedContentConfig(output_dimensionality=self.dim)
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(_is_transient),
            wait=self._wait,
            stop=stop_after_attempt(EMBED_ATTEMPTS),
            reraise=True,
        ):
            with attempt:
                response = await self._client.models.embed_content(
                    model=self.model, contents=content, config=config
                )
        embeddings = response.embeddings or []
        if len(embeddings) != 1 or not embeddings[0].values:
            raise ValueError(f"expected one embedding, got {len(embeddings)}")
        return list(embeddings[0].values)


def get_embedder(settings: Settings | None = None) -> Embedder:
    """The configured embedder, or exit if there is no API key."""
    return GeminiEmbedder(gemini_client(settings or get_settings()))


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
    parser.add_argument("--dry-run", action="store_true", help="text, size and cost, no call")
    parser.add_argument("--yes", action="store_true", help="confirm a paid run")
    args = parser.parse_args(argv)
    utf8_console()

    async with job_session() as session:
        pending = await select_pending(session, args.limit)
        if args.dry_run:
            films = await load_films(session, [movie_id for movie_id, _ in pending])
            summaries = dict(pending)
            texts = [build_embedding_text(f, summaries.get(f["id"])) for f in films]
            tokens = sum(len(t) for t in texts) / CHARS_PER_TOKEN
            usd = tokens * EMBEDDING_USD_PER_MTOK / 1_000_000
            print(
                f"{len(texts)} films ready to embed with {EMBEDDING_MODEL} at {EMBEDDING_DIM}-d, "
                f"~{tokens:,.0f} tokens in total, ~${usd:.4f} "
                f"(${EMBEDDING_USD_PER_MTOK}/MTok standard, paid tier)"
            )
            if texts:
                print("\n--- first text ---\n" + texts[0])
            return
        if not args.yes:
            raise SystemExit("paid run: re-run with --yes once the --dry-run cost is approved")
        stored = await embed_films(session, get_embedder(), pending)
        print(f"stored {stored} embeddings")


if __name__ == "__main__":
    asyncio.run(main())
