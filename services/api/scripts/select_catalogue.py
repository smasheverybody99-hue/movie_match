"""Pick the films to score: decade and language quotas over the films already ingested.

Usage, from services/api:

    python -m scripts.select_catalogue --target 500 --out ../../docs/catalogue-500.md

An ops tool, run by hand; the application never imports it. It reads DATABASE_URL in a
READ ONLY transaction and writes one Markdown file in the `--ids` format of
`app.pipelines.traits submit` (docs/review-films.md has the same shape).

Why it exists. `traits submit --limit 500` takes the 500 most popular pending films. On
our catalogue that is 220 films from the 2020s, none before 1950, and 94% English: the
recommender would learn recent Hollywood and little else (TZ FR-2; measured 2026-10-01).

The policy is the catalogue's own (app/pipelines/catalogue.py), applied to a smaller
target:

* `decade_quotas(target)`: the target split over decades 1920-2020 by DECADE_WEIGHTS;
* inside a decade, most popular first, while one original language holds at most
  `catalogue_max_language_share` (55%) of that decade's quota; if the cap leaves slots
  empty because other languages ran out, they are filled by popularity;
* films that already have traits are **pinned**: always in, counted in their decade's
  quota and their language's share, never scored again.

Why our catalogue is the pool, not TMDB (`ingest --plan-only --target 500`). That plan
was tried on 2026-10-01 ("option A"): it re-ranks TMDB by today's popularity, so it
changes from day to day; 6 of its 500 films were not in our catalogue (they would need
ingesting); it left out 6 of the 50 already-scored films; and with TMDB pools of only
3x the quota it ran out of other languages and came back 75% English (16 languages).
Over our 5,000 ingested films ("option B") the same policy gives 54% English, at most
55% in any decade, 26 languages, every pinned film, and the same answer every time
for the same database. Ties in popularity are broken by TMDB id.

Not yet covered by automated tests (backlog, docs/TZ.md §2), like scripts/migrate_db.py.
Checked by hand on 2026-10-01: 500 films, decades 6/13/19/25/31/38/50/69/87/100/62
(1920s-2020s), English 269, 26 languages, all 50 traited films included.
"""

import argparse
import asyncio
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.pipelines.catalogue import DECADE_WEIGHTS, decade_quotas
from app.pipelines.cli import utf8_console

FIRST_DECADE = min(DECADE_WEIGHTS)
LAST_DECADE = max(DECADE_WEIGHTS)


@dataclass(frozen=True)
class Film:
    id: int
    title: str
    year: int | None
    language: str
    popularity: float
    genres: str


def decade_of(year: int | None) -> int | None:
    """The quota decade; years outside 1920-2029 join the nearest end. None: no date."""
    if year is None:
        return None
    return max(FIRST_DECADE, min(LAST_DECADE, year // 10 * 10))


def select(
    films: Sequence[Film], pinned: set[int], target: int, max_language_share: float
) -> list[int]:
    """Ids in decade order; pinned films first inside their decade, then by popularity."""
    by_id = {f.id: f for f in films}
    chosen: list[int] = []
    for decade, quota in sorted(decade_quotas(target).items()):
        pins = sorted(
            (i for i in pinned if i in by_id and decade_of(by_id[i].year) == decade),
            key=lambda i: (-by_id[i].popularity, i),
        )
        picked = list(pins)
        cap = max(1, int(quota * max_language_share))
        per_language = Counter(by_id[i].language for i in pins)
        pool = sorted(
            (f for f in films if decade_of(f.year) == decade and f.id not in pinned),
            key=lambda f: (-f.popularity, f.id),
        )
        for film in pool:  # first pass: the language cap holds
            if len(picked) >= quota:
                break
            if per_language[film.language] < cap:
                picked.append(film.id)
                per_language[film.language] += 1
        taken = set(picked)
        for film in pool:  # second pass: fill what the cap left empty
            if len(picked) >= quota:
                break
            if film.id not in taken:
                picked.append(film.id)
                taken.add(film.id)
        chosen.extend(picked)
    return chosen


def describe(films: Mapping[int, Film], ids: Sequence[int]) -> tuple[str, str]:
    decades = Counter(decade_of(films[i].year) for i in ids)
    languages = Counter(films[i].language for i in ids)
    by_decade = ", ".join(f"{d}s {decades[d]}" for d in sorted(k for k in decades if k))
    by_language = ", ".join(f"{lang} {n}" for lang, n in languages.most_common(10))
    return by_decade, f"{by_language} ({len(languages)} languages)"


def markdown(
    films: Mapping[int, Film], ids: Sequence[int], pinned: set[int], target: int, share: float
) -> str:
    by_decade, by_language = describe(films, ids)
    english = sum(1 for i in ids if films[i].language == "en")
    rows = "\n".join(
        f"| {i} | {films[i].title.replace('|', '/')} | {films[i].year or ''} "
        f"| {films[i].language} | {films[i].genres} | |"
        for i in ids
    )
    quotas = ", ".join(f"{d}s {q}" for d, q in sorted(decade_quotas(target).items()))
    return f"""# Catalogue — {len(ids)} films to score (stage 2)

Generated by `python -m scripts.select_catalogue --target {target}` from the ingested
catalogue on {date.today().isoformat()}. Do not edit by hand: re-run the script.

## Selection policy

- **Pool:** the films already in our database (ingested from TMDB), not a fresh TMDB
  ranking, so the list is stable and needs no new ingestion.
- **Decade quotas:** `decade_quotas({target})` from `app/pipelines/catalogue.py`,
  the same weights the catalogue uses: {quotas}.
- **Language cap:** inside each decade one original language takes at most
  {share:.0%} of the quota (`catalogue_max_language_share`), more popular films first;
  slots the cap leaves empty are filled by popularity.
- **Pinned:** the {len(pinned)} films that already have traits (the stage-1 review list,
  `docs/review-films.md`) are always included and count towards their decade and
  language. They are not scored again: `traits submit` skips scored films.
- **Why not `ingest --plan-only`:** see the docstring of `scripts/select_catalogue.py`.

## Result

- {len(ids)} films. By decade: {by_decade}.
- By language: {by_language}. English {english} ({english / len(ids):.0%}).
- Already scored: {len(pinned & set(ids))}; to score: {len(ids) - len(pinned & set(ids))}.

## How it is used (from `services/api`)

```
python -m app.pipelines.traits submit --ids ../../docs/catalogue-500.md --dry-run
python -m app.pipelines.traits submit --ids ../../docs/catalogue-500.md --yes   # paid
```

## Films

| TMDB id | Title | Year | Lang | Genres | Verdict |
|---:|---|---:|---|---|---|
{rows}
"""


async def load(database_url: str) -> tuple[list[Film], set[int]]:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SET TRANSACTION READ ONLY"))
            rows = await conn.execute(
                text(
                    "SELECT m.id, m.title, extract(year from m.release_date)::int, "
                    "coalesce(m.original_language, ''), coalesce(m.popularity, 0), "
                    "coalesce(string_agg(g.name, ', ' ORDER BY g.name), '') "
                    "FROM movies m "
                    "LEFT JOIN movie_genres mg ON mg.movie_id = m.id "
                    "LEFT JOIN genres g ON g.id = mg.genre_id "
                    "WHERE m.adult IS NOT TRUE GROUP BY m.id"
                )
            )
            films = [Film(r[0], r[1], r[2], r[3], float(r[4]), r[5]) for r in rows]
            scored = {r[0] for r in await conn.execute(text("SELECT movie_id FROM movie_traits"))}
            await conn.rollback()
    finally:
        await engine.dispose()
    return films, scored


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--target", type=int, required=True, help="films in the list")
    parser.add_argument("--out", type=Path, required=True, help="Markdown file to write")
    args = parser.parse_args(argv)
    utf8_console()
    settings = get_settings()
    share = settings.catalogue_max_language_share

    films, scored = await load(settings.database_url)
    by_id = {f.id: f for f in films}
    ids = select(films, scored, args.target, share)
    missing = scored - set(ids)
    if missing:
        raise SystemExit(f"pinned films left out (no release date?): {sorted(missing)}")
    args.out.write_text(markdown(by_id, ids, scored, args.target, share), encoding="utf-8")
    by_decade, by_language = describe(by_id, ids)
    print(f"{len(ids)} films -> {args.out}")
    print(f"  by decade:   {by_decade}")
    print(f"  by language: {by_language}")
    print(
        f"  pinned (already scored): {len(scored & set(ids))}, to score: "
        f"{len(ids) - len(scored & set(ids))}"
    )


if __name__ == "__main__":
    asyncio.run(main())
