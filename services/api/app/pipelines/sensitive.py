"""Mark explicit or extreme films `movies.sensitive` (TZ backlog, NSFW; Phase 5).

    python -m app.pipelines.sensitive            # lists what it would mark, writes nothing
    python -m app.pipelines.sensitive --apply    # marks them
    python -m app.pipelines.sensitive --apply --skip 670,1232449   # all but these

TMDB's `adult` is for pornography and is false for these films, so they reached search,
onboarding and the film page (tester, 2026-10-13: Baise-moi, Caligula, Irreversible).
Two signals, as the user decided on 2026-11-17 (TMDB's age certification waits until
after the alpha - it needs an ingestion step):

* films whose trait extraction Google refused as PROHIBITED_CONTENT (`trait_failures`);
* the hand list below, by TMDB id.

A marked film is in no list - search, onboarding, recommendations, the assistant - and
its page warns before it shows. Marking only adds: a film is unmarked by hand.

Google's refusal is a blunt signal: in the 500-film selection it also refused films that
are not explicit (docs/catalogue-500.md). Read the list before --apply; --skip leaves
films out.
"""

import argparse
import asyncio
from collections.abc import Iterable, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie, TraitFailure
from app.pipelines.cli import read_ids, utf8_console
from app.pipelines.db import job_session

REFUSED = "PROHIBITED_CONTENT"

# TMDB id: title (year). Ids checked against TMDB's search on 2026-11-17.
HAND_LIST: dict[int, str] = {
    3134: "Baise-moi (2000)",
    9453: "Caligula (1979)",
    979: "Irreversible (2002)",
}


def refused(errors: Iterable[tuple[int, str]]) -> set[int]:
    """Films whose last trait error is Google's PROHIBITED_CONTENT refusal."""
    return {movie_id for movie_id, error in errors if REFUSED in (error or "")}


async def candidates(session: AsyncSession) -> list[tuple[int, str, bool]]:
    """(id, title, already marked) for every film either signal names that is in the
    catalogue, by id."""
    failures = (await session.execute(select(TraitFailure.movie_id, TraitFailure.last_error))).all()
    ids = refused((f.movie_id, f.last_error) for f in failures) | set(HAND_LIST)
    rows = await session.execute(
        select(Movie.id, Movie.title, Movie.sensitive).where(Movie.id.in_(ids)).order_by(Movie.id)
    )
    return [(r.id, r.title, r.sensitive) for r in rows.all()]


async def mark(session: AsyncSession, ids: Sequence[int]) -> int:
    """Set `sensitive` on these films; how many changed."""
    if not ids:
        return 0
    result = await session.execute(
        update(Movie)
        .where(Movie.id.in_(ids), Movie.sensitive.is_(False))
        .values(sensitive=True)
        .execution_options(synchronize_session=False)
    )
    await session.commit()
    return int(result.rowcount or 0)  # type: ignore[attr-defined]


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Mark explicit or extreme films sensitive.")
    parser.add_argument("--apply", action="store_true", help="write; without it, only list")
    parser.add_argument("--skip", default="", help="TMDB ids not to mark, e.g. 670,1232449")
    args = parser.parse_args(argv)
    skip = set(read_ids(args.skip)) if args.skip else set()
    utf8_console()
    async with job_session() as session:
        found = await candidates(session)
        for movie_id, title, marked in found:
            note = "  (already marked)" if marked else "  (skipped)" if movie_id in skip else ""
            print(f"{movie_id:>8}  {title}{note}")
        missing = sorted(set(HAND_LIST) - {movie_id for movie_id, _, _ in found})
        if missing:
            print("hand list, not in the catalogue: " + ", ".join(map(str, missing)))
        todo = [movie_id for movie_id, _, marked in found if not marked and movie_id not in skip]
        if not args.apply:
            print(f"{len(todo)} to mark; nothing written (add --apply)")
            return
        print(f"marked {await mark(session, todo)}")


if __name__ == "__main__":
    asyncio.run(main())
