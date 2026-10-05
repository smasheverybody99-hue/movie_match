"""Recommendations: retrieve by embedding, rank by trait match, diversify, group into sections.

Embeddings for retrieval, traits for ranking (docs/architecture.md):

1. Retrieve ~300 candidates by pgvector ANN over movie embeddings. The query vector is
   the user's taste in embedding space: the mean of the embeddings of the films they
   liked, weighted exactly as the taste vector weighs them (taste.rating_weight).
2. Hard filters in SQL: not adult, has traits, not rated, not watched, not dismissed,
   plus the section's own filter (runtime for "Under 90 minutes").
3. Score every candidate with matching.match_percentage (docs/TZ.md FR-5), give it its
   band (services/bands.py), and drop the user's furthest share of the catalogue
   (match_floor_share; this replaced a fixed 60% cut, TZ 1.13).
4. Diversify with MMR over the best 3·k of them (relevance = match / 100, similarity =
   embedding cosine similarity between the two films), allowing at most 2 films per
   director in a section. Not trait closeness: the best match sits next to the user's
   taste, so "far from what is picked" would mean "far from the taste" and MMR could
   never prefer a different film over a near-duplicate. Embeddings tell a sequel from
   a different film with the same traits.

A film appears in at most one section; sections are filled in the order below. The
pure part (score, pick) takes plain data and is unit-tested without a database.
"""

import math
import uuid
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import Select

from app.models import (
    Credit,
    Dismissal,
    Movie,
    MovieEmbedding,
    MovieTraits,
    Rating,
    User,
    WatchlistItem,
)
from app.services.bands import load_cuts
from app.services.matching import (
    BandCuts,
    MatchBand,
    ReasonRule,
    match_band,
    match_percentage,
    match_raw,
    top_reasons,
    weights_vector,
)
from app.services.mmr import mmr
from app.services.reasons import load_rule
from app.services.taste import HIGH_RATING, RatedFilm, rating_weight

MIN_RATINGS = 10  # FR-3: no recommendations before 10 ratings
MAX_PER_DIRECTOR = 2  # FR-5: per section
CANDIDATES = 300
SECTION_SIZE = {"for_you": 20, "because_you_loved": 10, "under_90": 10, "outside_usual": 10}
SHORT_RUNTIME = 90  # minutes, inclusive
POOL_FACTOR = 3  # MMR chooses a section of k from the best POOL_FACTOR·k by match
# HNSW's search breadth. "Outside your usual taste" reads the ring of films ranked
# CANDIDATES..2·CANDIDATES by distance, so the index must look at least that far.
EF_SEARCH = 1000

SectionKey = Literal["for_you", "because_you_loved", "under_90", "outside_usual"]


@dataclass(frozen=True)
class Candidate:
    movie: Movie
    vector: Sequence[float]  # traits, TRAIT_KEYS order
    directors: frozenset[int] = frozenset()


@dataclass(frozen=True)
class Scored:
    candidate: Candidate
    match: int
    reasons: list[str]
    band: MatchBand | None = None

    @property
    def movie_id(self) -> int:
        return self.candidate.movie.id


@dataclass(frozen=True)
class Section:
    key: SectionKey
    items: list[Scored]
    seed: Movie | None = None


@dataclass(frozen=True)
class Recommendations:
    rating_count: int
    sections: list[Section] = field(default_factory=list)

    @property
    def ratings_needed(self) -> int:
        return max(MIN_RATINGS - self.rating_count, 0)


# --- pure part ------------------------------------------------------------------------


def score(
    candidates: Sequence[Candidate],
    taste: Sequence[float],
    weights: Sequence[float],
    rule: ReasonRule | None,
    cuts: BandCuts | None = None,
) -> list[Scored]:
    """Match and band every candidate; drop those below the floor cut; best first.
    Without a reason rule (no catalogue statistics yet) the reasons are empty; without
    cuts (no film has traits) nothing is dropped and no film has a band."""
    scored = []
    for candidate in candidates:
        raw = match_raw(taste, weights, candidate.vector)
        if cuts is not None and raw < cuts.floor:
            continue
        reasons = top_reasons(taste, candidate.vector, rule, weights=weights) if rule else []
        scored.append(
            Scored(
                candidate,
                match_percentage(taste, weights, candidate.vector),
                reasons,
                match_band(raw, cuts),
            )
        )
    return sorted(scored, key=lambda s: (-s.match, s.movie_id))


Similarity = Callable[[Scored, Scored], float]


def _director_cap(item: Scored, picked: Sequence[Scored]) -> bool:
    counts = Counter(d for p in picked for d in p.candidate.directors)
    return all(counts[d] < MAX_PER_DIRECTOR for d in item.candidate.directors)


def shortlist(scored: Sequence[Scored], k: int, exclude: set[int] | None = None) -> list[Scored]:
    """The best POOL_FACTOR·k of `scored` (best first) that are not in `exclude`."""
    exclude = exclude or set()
    return [s for s in scored if s.movie_id not in exclude][: POOL_FACTOR * k]


def pick(pool: Sequence[Scored], k: int, similarity: Similarity) -> list[Scored]:
    """Up to k films from `pool`: MMR, at most MAX_PER_DIRECTOR per director."""
    return mmr(
        pool,
        relevance=lambda s: s.match / 100.0,
        similarity=similarity,
        k=k,
        admissible=_director_cap,
    )


def taste_embedding(
    films: Sequence[tuple[RatedFilm, Sequence[float]]], now: datetime
) -> list[float] | None:
    """Weighted mean of liked films' unit-length embeddings; None if nothing is liked."""
    total = 0.0
    acc: list[float] | None = None
    for film, embedding in films:
        weight = rating_weight(film, now)
        norm = math.sqrt(sum(v * v for v in embedding))
        if weight == 0 or norm == 0:
            continue
        if acc is None:
            acc = [0.0] * len(embedding)
        for i, v in enumerate(embedding):
            acc[i] += weight * v / norm
        total += weight
    if acc is None:
        return None
    return [v / total for v in acc]


# --- database side --------------------------------------------------------------------


async def movie_exists(session: AsyncSession, movie_id: int) -> bool:
    return await session.get(Movie, movie_id) is not None


async def rating_count(session: AsyncSession, user_id: uuid.UUID) -> int:
    count = await session.scalar(
        select(func.count()).select_from(Rating).where(Rating.user_id == user_id)
    )
    return count or 0


async def seen_ids(session: AsyncSession, user_id: uuid.UUID) -> set[int]:
    """Rated, watched or dismissed: never recommended."""
    rated = select(Rating.movie_id).where(Rating.user_id == user_id)
    watched = select(WatchlistItem.movie_id).where(
        WatchlistItem.user_id == user_id, WatchlistItem.watched_at.is_not(None)
    )
    dismissed = select(Dismissal.movie_id).where(Dismissal.user_id == user_id)
    rows = await session.scalars(rated.union(watched, dismissed))
    return set(rows.all())


async def _liked_with_embeddings(
    session: AsyncSession, user_id: uuid.UUID
) -> list[tuple[RatedFilm, Sequence[float], Movie]]:
    rows = await session.execute(
        select(Rating.score, Rating.updated_at, MovieTraits.vector, MovieEmbedding.embedding, Movie)
        .join(MovieTraits, MovieTraits.movie_id == Rating.movie_id)
        .join(MovieEmbedding, MovieEmbedding.movie_id == Rating.movie_id)
        .join(Movie, Movie.id == Rating.movie_id)
        .where(Rating.user_id == user_id)
        .order_by(Rating.score.desc(), Rating.updated_at.desc(), Rating.movie_id)
    )
    return [
        (RatedFilm(score=s, rated_at=at, vector=[float(v) for v in vec]), list(emb), movie)
        for s, at, vec, emb, movie in rows.all()
    ]


def _candidates_query(query_vector: Sequence[float], exclude: set[int]) -> Select:
    distance = MovieEmbedding.embedding.cosine_distance(query_vector)
    directors = (
        select(func.array_agg(Credit.person_id))
        .where(Credit.movie_id == Movie.id, Credit.job == "Director")
        .correlate(Movie)
        .scalar_subquery()
    )
    stmt = (
        select(Movie, MovieTraits.vector, directors)
        .join(MovieEmbedding, MovieEmbedding.movie_id == Movie.id)
        .join(MovieTraits, MovieTraits.movie_id == Movie.id)
        .where(Movie.adult.is_(False))
        .order_by(distance, Movie.id)
    )
    if exclude:
        stmt = stmt.where(Movie.id.not_in(exclude))
    return stmt


async def embedding_similarities(
    session: AsyncSession, movie_ids: Sequence[int]
) -> dict[frozenset[int], float]:
    """Cosine similarity of every pair of the films' embeddings, in one query.

    Computed in the database so no 1,536-d vector crosses the network; a shortlist of
    60 films is 1,770 small rows.
    """
    if len(movie_ids) < 2:
        return {}
    a, b = aliased(MovieEmbedding), aliased(MovieEmbedding)
    rows = await session.execute(
        select(a.movie_id, b.movie_id, 1 - a.embedding.cosine_distance(b.embedding))
        .join(b, a.movie_id < b.movie_id)
        .where(a.movie_id.in_(movie_ids), b.movie_id.in_(movie_ids))
    )
    return {frozenset((x, y)): float(sim) for x, y, sim in rows.all()}


async def tune_index_search(session: AsyncSession) -> None:
    """Search settings for this transaction, in one round trip.

    ef_search: how far HNSW looks (see EF_SEARCH). iterative_scan: filters are applied
    after the index proposes rows, so keep scanning until enough rows survive them
    (pgvector 0.8).
    """
    await session.execute(
        text(
            "SELECT set_config('hnsw.ef_search', :ef, true),"
            " set_config('hnsw.iterative_scan', 'relaxed_order', true)"
        ),
        {"ef": str(EF_SEARCH)},
    )


async def retrieve(
    session: AsyncSession,
    query_vector: Sequence[float],
    exclude: set[int],
    *,
    limit: int = CANDIDATES,
    offset: int = 0,
    max_runtime: int | None = None,
) -> list[Candidate]:
    """Nearest films to `query_vector` in embedding space, after the hard filters.

    Call `tune_index_search` once in the same transaction first.
    """
    stmt = _candidates_query(query_vector, exclude)
    if max_runtime is not None:
        stmt = stmt.where(Movie.runtime_minutes <= max_runtime)
    stmt = stmt.offset(offset).limit(limit)
    rows = (await session.execute(stmt)).all()
    return [
        Candidate(
            movie=movie,
            vector=[float(v) for v in vector],
            directors=frozenset(d for d in (director_ids or []) if d is not None),
        )
        for movie, vector, director_ids in rows
    ]


async def recommend(
    session: AsyncSession, user_id: uuid.UUID, now: datetime | None = None
) -> Recommendations:
    """The user's sections, or none with `ratings_needed` > 0 below MIN_RATINGS."""
    now = now or datetime.now(UTC)
    count = await rating_count(session, user_id)
    if count < MIN_RATINGS:
        return Recommendations(rating_count=count)

    user = await session.get(User, user_id, populate_existing=True)
    if user is None or user.taste_vector is None or not user.taste_weights:
        return Recommendations(rating_count=count)
    taste = [float(v) for v in user.taste_vector]
    weights = weights_vector(user.taste_weights)

    liked = await _liked_with_embeddings(session, user_id)
    query = taste_embedding([(film, emb) for film, emb, _ in liked], now)
    if query is None:
        return Recommendations(rating_count=count)

    exclude = await seen_ids(session, user_id)
    rule = await load_rule(session)
    cuts = await load_cuts(session, user_id, user.taste_updated_at, taste, weights)
    await tune_index_search(session)
    shown: set[int] = set()
    sections: list[Section] = []

    async def add(key: SectionKey, candidates: list[Candidate], seed: Movie | None = None) -> None:
        k = SECTION_SIZE[key]
        pool = shortlist(score(candidates, taste, weights, rule, cuts), k, exclude=shown)
        sims = await embedding_similarities(session, [s.movie_id for s in pool])
        items = pick(pool, k, lambda x, y: sims.get(frozenset((x.movie_id, y.movie_id)), 0.0))
        if items:
            sections.append(Section(key=key, items=items, seed=seed))
            shown.update(s.movie_id for s in items)

    await add("for_you", await retrieve(session, query, exclude))

    favourite = next(
        ((film, emb, movie) for film, emb, movie in liked if film.score >= HIGH_RATING), None
    )
    if favourite is not None:
        _, seed_embedding, seed_movie = favourite
        await add("because_you_loved", await retrieve(session, seed_embedding, exclude), seed_movie)

    await add("under_90", await retrieve(session, query, exclude, max_runtime=SHORT_RUNTIME))
    await add("outside_usual", await retrieve(session, query, exclude, offset=CANDIDATES))

    return Recommendations(rating_count=count, sections=sections)
