# Architecture

```
TMDB  ──(nightly job)──►  Postgres (movies, credits, keywords)
                                │
                                ├──► trait pipeline (Claude Haiku, Batch API)
                                │        └──► movie_traits (14-dim vector)
                                │
                                └──► embedding job ──► movie_embeddings (pgvector, HNSW)

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
         explanation (Haiku, cached per user+movie)  ──►  API  ──►  web / mobile
```

## Why this shape

**Trait vector, not just embeddings.** An embedding tells you two films are similar; it
cannot tell a user *why*. The 14 named dimensions are what make "you may like this because
it combines psychological complexity and a major reveal" possible, and what makes a wrong
recommendation debuggable.

**Embeddings for retrieval, traits for ranking.** ANN over embeddings is fast over 20k+
rows; exact trait scoring over a few hundred candidates is cheap and interpretable.

**LLM off the request path.** Trait extraction runs as a batch job. Explanations are
generated once per (user, movie) and cached. The only live LLM call is the assistant, and
it is rate-limited per user.

## Match percentage

```
match = 100 * (1 - weighted_cosine_distance(user_taste_vector, movie_trait_vector))
```

Weights come from how consistently the user rates on each dimension: a dimension the user
is indifferent about gets a low weight. The formula lives in `app/services/matching.py`
and is unit-tested with hand-written vectors.

## Services boundary

The API is one deployable. Background jobs (ingestion, trait extraction, embeddings) run
as separate worker processes from the same codebase under `app/pipelines/`, invoked by a
scheduler, never by an HTTP request.
