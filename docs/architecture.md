# Architecture

```
TMDB  ──(nightly job)──►  Postgres (movies, credits, keywords)
                                │
                                ├──► trait pipeline (Gemini Flash-Lite, Batch API)
                                │        └──► movie_traits (14-dim vector)
                                │
                                └──► embedding job (Gemini Embedding 2, 1,536-d) ──► movie_embeddings (pgvector, HNSW)

User actions (ratings, favourites, watchlist)
        │
        └──► taste vector (weighted mean of rated movies' trait vectors)
                    │
                    ▼
         candidate retrieval (pgvector ANN + hard filters)
                    │
                    ▼
         re-rank: trait distance + popularity damping + MMR diversity + seen-exclusion
                    │
                    ▼
         explanation (Gemini Flash-Lite, cached per user+movie)  ──►  API  ──►  web / mobile
```

## Why this shape

**Trait vector, not just embeddings.** An embedding tells you two films are similar; it
cannot tell a user *why*. The 14 named dimensions are what make "you may like this because
it combines psychological complexity and a major reveal" possible, and what makes a wrong
recommendation debuggable.

**Embeddings for retrieval, traits for ranking.** ANN over embeddings is fast over 20k+
rows; exact trait scoring over a few hundred candidates is cheap and interpretable.

**LLM off the request path.** Trait extraction runs as a batch job. `GET /recommendations`
never calls an LLM: it attaches explanations already cached. The client asks
`GET /recommendations/{id}/explanation` per card; that checks the cache (per user, film
and language) first and generates only on a miss, capped per user per day
(`explanation_daily_calls_per_user`). The other live LLM call is the assistant, also
rate-limited per user.

## Match percentage

The formula is docs/TZ.md FR-5 (a weighted distance; it replaced a weighted-cosine form
on 2026-09-27, because on all-positive 0..100 vectors cosine rates nearly any two films
80–95% alike and ignores size — a taste of 30 everywhere matched a film of 90 everywhere
at 100%):

```
d     = sqrt( Σ w[i] * (taste[i] - movie[i])² / Σ w[i] ) / 100
match = round( 100 * (1 - d) )          # rounded half up
```

Weights come from how consistently the user rates on each dimension: a dimension the user
is indifferent about gets a low weight. The formula lives in `app/services/matching.py`
and is unit-tested with hand-written vectors.

## Services boundary

The API is one deployable. Background jobs (ingestion, trait extraction, embeddings) run
as separate worker processes from the same codebase under `app/pipelines/`, invoked by a
scheduler, never by an HTTP request.
