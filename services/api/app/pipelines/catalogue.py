"""Which films make up the catalogue.

Popularity alone gives a catalogue of recent Hollywood. Instead the target is split into
decade quotas, and within each decade no single original language may take more than
`max_language_share` of the quota while other languages still have candidates. Inside
those constraints, more popular films win.

`select_catalogue` is pure: it takes candidate pools and returns ids, so the policy is
testable without TMDB. `build_pools` is the part that talks to TMDB.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.pipelines.tmdb import Candidate, TmdbClient

# Relative weight of each decade (start year) in the catalogue. Older decades are
# represented but thinner: fewer of their films are still widely known.
DECADE_WEIGHTS: dict[int, int] = {
    1920: 1,
    1930: 2,
    1940: 3,
    1950: 4,
    1960: 5,
    1970: 6,
    1980: 8,
    1990: 11,
    2000: 14,
    2010: 16,
    2020: 10,
}

# How many candidates to fetch per quota slot. More headroom = more room for the
# language cap to find non-dominant languages.
POOL_FACTOR = 3
MAX_TMDB_PAGES = 500  # /discover refuses pages beyond this


@dataclass(frozen=True)
class Selection:
    ids: list[int]
    by_decade: dict[int, int]
    by_language: dict[str, int]


def decade_quotas(target: int, weights: Mapping[int, int] = DECADE_WEIGHTS) -> dict[int, int]:
    """Split `target` across decades by weight. Always sums to exactly `target`."""
    if target <= 0:
        return {decade: 0 for decade in weights}
    total = sum(weights.values())
    raw = {d: target * w / total for d, w in weights.items()}
    quotas = {d: int(v) for d, v in raw.items()}
    # Hand out the rounding remainder to the largest fractional parts.
    remainder = target - sum(quotas.values())
    for decade in sorted(raw, key=lambda d: raw[d] - quotas[d], reverse=True)[:remainder]:
        quotas[decade] += 1
    return quotas


def pick_decade(pool: Sequence[Candidate], quota: int, max_language_share: float) -> list[int]:
    """Choose up to `quota` films from one decade's pool.

    First pass: most popular first, skipping a film if its language already holds its
    cap. Second pass: if the cap left slots empty because the pool ran out of other
    languages, fill them by popularity regardless of language - a full catalogue beats a
    perfectly balanced short one.
    """
    ranked = sorted(pool, key=lambda c: (-c.popularity, c.id))
    cap = max(1, int(quota * max_language_share))
    chosen: list[int] = []
    seen: set[int] = set()
    per_language: Counter[str] = Counter()

    for candidate in ranked:
        if len(chosen) == quota:
            break
        if candidate.id in seen or per_language[candidate.language] >= cap:
            continue
        chosen.append(candidate.id)
        seen.add(candidate.id)
        per_language[candidate.language] += 1

    for candidate in ranked:
        if len(chosen) == quota:
            break
        if candidate.id not in seen:
            chosen.append(candidate.id)
            seen.add(candidate.id)

    return chosen


def select_catalogue(
    pools: Mapping[int, Sequence[Candidate]],
    target: int,
    max_language_share: float,
    weights: Mapping[int, int] = DECADE_WEIGHTS,
) -> Selection:
    """Candidate pools per decade -> the ordered list of film ids to ingest."""
    quotas = decade_quotas(target, weights)
    ids: list[int] = []
    taken: set[int] = set()
    by_decade: dict[int, int] = {}
    language_of = {c.id: c.language for pool in pools.values() for c in pool}

    for decade in sorted(quotas):
        pool = [c for c in pools.get(decade, []) if c.id not in taken]
        picked = pick_decade(pool, quotas[decade], max_language_share)
        ids.extend(picked)
        taken.update(picked)
        by_decade[decade] = len(picked)

    by_language = Counter(language_of[i] for i in ids)
    return Selection(ids=ids, by_decade=by_decade, by_language=dict(by_language.most_common()))


async def build_pools(
    client: TmdbClient,
    target: int,
    min_votes: int,
    weights: Mapping[int, int] = DECADE_WEIGHTS,
) -> dict[int, list[Candidate]]:
    """Fetch POOL_FACTOR x quota candidates per decade from TMDB discovery."""
    pools: dict[int, list[Candidate]] = {}
    for decade, quota in decade_quotas(target, weights).items():
        wanted = quota * POOL_FACTOR
        pool: list[Candidate] = []
        page, total_pages = 1, 1
        while len(pool) < wanted and page <= min(total_pages, MAX_TMDB_PAGES):
            candidates, total_pages = await client.discover(
                page=page, year_from=decade, year_to=decade + 9, min_votes=min_votes
            )
            pool.extend(candidates)
            page += 1
        pools[decade] = pool
    return pools
