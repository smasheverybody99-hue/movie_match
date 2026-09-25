"""Trait extraction: movie -> 14-dimension Movie DNA vector.

    python -m app.pipelines.traits submit --limit 50 --dry-run   # prompt + cost, no API call
    python -m app.pipelines.traits submit --limit 50 --yes       # real, paid batch
    python -m app.pipelines.traits submit --ids ../../docs/review-films.md --dry-run
    python -m app.pipelines.traits collect <batch_id>
    python -m app.pipelines.traits status

Runs as a batch job, never inside a request. Uses Claude Haiku through the Batch API,
which halves the token cost. Runs are staged (CLAUDE.md): 50 films, check by hand, then
500, then the rest - `--limit` has no default so every run states its size. `--ids`
takes a hand-picked list instead (ids, or a file such as docs/review-films.md).
"""

import argparse
import asyncio
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

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
from app.traits import SPEC_VERSION, TRAIT_KEYS, to_vector

MODEL = "claude-haiku-4-5"
MAX_TOKENS = 1024  # expected output is ~250 tokens; the ceiling only guards truncation
MAX_ATTEMPTS = 2  # first try + one retry, then the film is recorded as failed

# Claude Haiku 4.5, Batch API (50% of the $1 / $5 standard rate), USD per million tokens.
BATCH_INPUT_USD_PER_MTOK = 0.50
BATCH_OUTPUT_USD_PER_MTOK = 2.50
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


def build_request(film: dict[str, Any]) -> dict[str, Any]:
    """One film -> one Message Batches request."""
    return {
        "custom_id": custom_id(film["id"]),
        "params": {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": build_prompt(film)}],
        },
    }


@dataclass(frozen=True)
class CostEstimate:
    films: int
    input_tokens: int
    output_tokens: int

    @property
    def usd(self) -> float:
        return (
            self.input_tokens * BATCH_INPUT_USD_PER_MTOK
            + self.output_tokens * BATCH_OUTPUT_USD_PER_MTOK
        ) / 1_000_000

    def scaled_to(self, films: int) -> "CostEstimate":
        """Same per-film averages, different film count."""
        if self.films == 0:
            return CostEstimate(films, 0, 0)
        ratio = films / self.films
        return CostEstimate(
            films, round(self.input_tokens * ratio), round(self.output_tokens * ratio)
        )


def estimate_cost(films: Sequence[dict[str, Any]]) -> CostEstimate:
    """Approximate batch cost from prompt length. No API call."""
    per_request_overhead = len(SYSTEM_PROMPT) + 20  # system prompt + message framing
    chars = sum(per_request_overhead + len(build_prompt(f)) for f in films)
    return CostEstimate(
        films=len(films),
        input_tokens=math.ceil(chars / CHARS_PER_TOKEN),
        output_tokens=EXPECTED_OUTPUT_TOKENS * len(films),
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


async def store_traits(session: AsyncSession, movie_id: int, parsed: dict[str, Any]) -> None:
    scores = parsed["scores"]
    values = {
        "movie_id": movie_id,
        "scores": scores,
        "vector": to_vector(scores),
        "summary": parsed["summary"],
        "model": MODEL,
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


async def record_failure(session: AsyncSession, movie_id: int, error: str) -> None:
    stmt = insert(TraitFailure).values(movie_id=movie_id, attempts=1, last_error=error[:2000])
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[TraitFailure.movie_id],
            set_={
                "attempts": TraitFailure.attempts + 1,
                "last_error": stmt.excluded.last_error,
                "updated_at": func.now(),
            },
        )
    )


# --- Anthropic side ---------------------------------------------------------------


class BatchesClient(Protocol):
    """The slice of AsyncAnthropic this module uses. Tests pass a fake."""

    @property
    def messages(self) -> Any: ...


async def submit(session: AsyncSession, client: BatchesClient, films: Sequence[dict]) -> str:
    batch = await client.messages.batches.create(requests=[build_request(f) for f in films])
    session.add(
        TraitBatch(
            id=batch.id,
            movie_ids=[f["id"] for f in films],
            model=MODEL,
            status="submitted",
        )
    )
    await session.commit()
    return batch.id


@dataclass
class CollectResult:
    stored: int = 0
    failed: int = 0


async def collect(session: AsyncSession, client: BatchesClient, batch_id: str) -> CollectResult:
    """Store every valid result; count every malformed or errored one as an attempt."""
    outcome = CollectResult()
    async for item in await client.messages.batches.results(batch_id):
        movie_id = movie_id_from(item.custom_id)
        error = None
        if item.result.type == "succeeded":
            message = item.result.message
            text = next((b.text for b in message.content if b.type == "text"), "")
            if message.stop_reason == "max_tokens":
                error = "truncated at max_tokens"
            else:
                try:
                    await store_traits(session, movie_id, parse_response(text))
                    outcome.stored += 1
                    continue
                except ValueError as exc:
                    error = f"malformed: {exc}"
        else:
            error = f"batch result {item.result.type}"
        await record_failure(session, movie_id, error)
        outcome.failed += 1

    batch = await session.get(TraitBatch, batch_id)
    if batch is not None:
        batch.status = "collected"
        batch.collected_at = datetime.now(UTC)
    await session.commit()
    return outcome


# --- CLI ----------------------------------------------------------------------------


def _print_estimate(estimate: CostEstimate, catalogue: int) -> None:
    rates = f"${BATCH_INPUT_USD_PER_MTOK} in / ${BATCH_OUTPUT_USD_PER_MTOK} out per MTok"
    print(f"model {MODEL} via Batch API ({rates})")
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
            catalogue = await session.scalar(select(func.count()).select_from(Movie)) or 0
            _print_estimate(estimate_cost(films), catalogue)
            if args.dry_run:
                if films:
                    print("\n--- system prompt ---\n" + SYSTEM_PROMPT)
                    print("\n--- first film ---\n" + build_prompt(films[0]))
                return
            if not args.yes:
                raise SystemExit("paid run: re-run with --yes once the estimate is approved")
            if not settings.anthropic_api_key:
                raise SystemExit("ANTHROPIC_API_KEY is not configured")
            import anthropic  # imported here so dry runs work without the key

            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            for start in range(0, len(films), settings.trait_batch_size):
                chunk = films[start : start + settings.trait_batch_size]
                print(f"submitted batch {await submit(session, client, chunk)}: {len(chunk)} films")
            return

        if not settings.anthropic_api_key:
            raise SystemExit("ANTHROPIC_API_KEY is not configured")
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        status = await client.messages.batches.retrieve(args.batch_id)
        if status.processing_status != "ended":
            raise SystemExit(f"batch {args.batch_id} is {status.processing_status}; try later")
        result = await collect(session, client, args.batch_id)
        print(f"stored {result.stored}, failed {result.failed}")


if __name__ == "__main__":
    asyncio.run(main())
