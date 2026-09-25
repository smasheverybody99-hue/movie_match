"""Trait scores for hand review.

    python -m app.pipelines.report 27205 157336 680     # by TMDB id

Prints one row per film, one column per trait, so a person who knows the films can say
whether the scores are right. Films without traits are listed as such, not skipped.
"""

import argparse
import asyncio
from collections.abc import Sequence

from sqlalchemy import select

from app.models import Movie, MovieTraits
from app.pipelines.db import job_session
from app.traits import TRAIT_KEYS

TITLE_WIDTH = 28


def _abbreviation(key: str) -> str:
    """psychological_complexity -> psy_com: short, still recognisable column headers."""
    return "_".join(part[:3] for part in key.split("_"))


def format_report(rows: Sequence[tuple[int, str, int | None, dict | None]]) -> str:
    """(id, title, year, scores or None) rows -> fixed-width table."""
    headers = [_abbreviation(k) for k in TRAIT_KEYS]
    width = max(len(h) for h in headers)
    lines = [
        f"{'id':>8}  {'title':<{TITLE_WIDTH}}  {'year':>4}  "
        + " ".join(f"{h:>{width}}" for h in headers)
    ]
    for movie_id, title, year, scores in rows:
        name = title if len(title) <= TITLE_WIDTH else title[: TITLE_WIDTH - 1] + "…"
        prefix = f"{movie_id:>8}  {name:<{TITLE_WIDTH}}  {year or '':>4}  "
        if scores is None:
            lines.append(prefix + "(no traits yet)")
        else:
            lines.append(prefix + " ".join(f"{round(scores[k]):>{width}}" for k in TRAIT_KEYS))
    lines.append("")
    lines.append("columns: " + ", ".join(f"{_abbreviation(k)}={k}" for k in TRAIT_KEYS))
    return "\n".join(lines)


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trait scores for hand review.")
    parser.add_argument("ids", nargs="+", type=int, help="TMDB film ids")
    args = parser.parse_args(argv)

    async with job_session() as session:
        stmt = (
            select(Movie.id, Movie.title, Movie.release_date, MovieTraits.scores)
            .outerjoin(MovieTraits, MovieTraits.movie_id == Movie.id)
            .where(Movie.id.in_(args.ids))
        )
        found = {r.id: r for r in (await session.execute(stmt)).all()}
    rows = [
        (
            i,
            found[i].title,
            found[i].release_date.year if found[i].release_date else None,
            found[i].scores,
        )
        for i in args.ids
        if i in found
    ]
    missing = [i for i in args.ids if i not in found]
    print(format_report(rows))
    if missing:
        print(f"not in the catalogue: {', '.join(map(str, missing))}")


if __name__ == "__main__":
    asyncio.run(main())
