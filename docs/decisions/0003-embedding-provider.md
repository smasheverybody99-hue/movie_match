# ADR 0003 — Embedding provider

Date: 2026-09-25 · Status: **resolved by [ADR 0004](0004-llm-provider.md)** (2026-09-26): Gemini `gemini-embedding-2` at 1,536 dimensions, no migration

## Context

Movie Match uses embeddings for retrieval (ANN over `movie_embeddings`, HNSW index) and
trait vectors for ranking (architecture.md). Anthropic has no embeddings API, so this is
a second provider. Nothing in the stack decisions (ADR 0001, CLAUDE.md) chose one.

Phase 1 was built so the choice can wait: `app/pipelines/embeddings.py` works against an
`Embedder` protocol, tests use a fake, and `get_embedder()` refuses to run until a
provider is wired in. Wiring one in is one class, one setting and — if its size is not
1536 — one migration.

### What we are embedding

- 5,000 films (settings.catalogue_target); may grow to 20,000+.
- Text per film: title + year, genres, keywords, overview, trait summary.
  Measured on the real catalogue: **~940,000 tokens for all 5,000 films**
  (~190 tokens each; estimated from length, a real run will count exactly).
- Mostly English: TMDB overviews come back in English; titles are often not.
- **Later (Phase 4 assistant):** user queries, often in **Uzbek**, will be embedded at
  request time and matched against English film text. Cross-lingual quality and request
  latency matter then, not now.

### Hard constraints

- **pgvector HNSW indexes the `vector` type up to 2,000 dimensions.** Larger outputs
  (3,072, or 2,048) need `halfvec` or a smaller output size. Current column: 1536.
- Dimension is fixed per column: changing provider later means re-embedding everything
  (cheap, see below) plus a migration.
- CLAUDE.md: no LLM or embedding call inside a request handler without a cache lookup
  first; keys in `.env` only.

## Options

Prices checked on the providers' pages on 2026-09-25. Cost is for the ~0.94M-token
catalogue; ×4 for a 20,000-film catalogue.

| Option | Dims (default) | Fits current 1536 column? | 5,000 films | Needs |
|---|---|---|---|---|
| **Voyage `voyage-4`** | 1024 (256/512/2048 also) | No — migration to 1024 | ~$0.06, and inside the 200M free tokens | `VOYAGE_API_KEY`, `voyageai` SDK |
| Voyage `voyage-4-lite` | 1024 | No — migration | ~$0.02 (free tier) | same |
| Voyage `voyage-4-large` | 1024 | No — migration | ~$0.11 (free tier) | same |
| **OpenAI `text-embedding-3-small`** | 1536 | **Yes** — no migration | ~$0.02 | `OPENAI_API_KEY`, `openai` SDK |
| OpenAI `text-embedding-3-large` | 3072 | No — over the HNSW limit; use `dimensions=1536` or `halfvec` | ~$0.12 | same |
| Local open model (e.g. sentence-transformers) | model-dependent | depends | $0 | PyTorch (~GBs); Smart App Control on the dev machine blocked SQLAlchemy 2.1's DLLs and may block PyTorch's |

Voyage free allowance: 200M tokens per account for the `voyage-4` family — about 200
full re-embeddings of this catalogue.

### What differs besides price

Price is negligible for every hosted option — cents per full catalogue. The real
differences:

- **Anthropic alignment.** Voyage is the embeddings provider Anthropic's documentation
  points to. One fewer vendor relationship if we later consolidate; not a technical need.
- **Migration.** OpenAI `3-small` drops into the existing 1536 column with no schema
  change. Voyage needs a migration (1536 → 1024), trivial while the table is empty.
- **Cross-lingual queries (Phase 4).** Voyage lists the `voyage-4` family as
  multilingual. Uzbek-to-English retrieval quality is unverified for every option; test
  it with 20 real Uzbek queries before Phase 4 commits.
- **Request-time latency (Phase 4).** Every hosted option adds a network call per new
  query; the cache rule applies either way. A local model avoids it but costs the
  install weight above.

## Decision

Resolved by ADR 0004: Gemini Embedding 2 at 1,536 dimensions. None of the options
below was taken; the analysis is kept as the record of what was considered.

A reasonable default if no one has a preference: **`voyage-4` at 1024 dims** — free at
this scale, multilingual, and the documented partner for our LLM vendor. Pick OpenAI
`3-small` instead if avoiding the migration or a second new vendor matters more.

## Consequences (once decided)

- Add the key to `.env` / `.env.example`, the SDK to `pyproject.toml` (say why, per the
  phase rules), and one `Embedder` implementation.
- If the size is not 1536: migration `0003` changes `movie_embeddings.embedding` and
  rebuilds the HNSW index; update `EMBEDDING_DIM`.
- Run staged like traits: dry-run, 50, check neighbours by eye, then all.
- Record the chosen model per row (`movie_embeddings.model` already exists), so a future
  switch can re-embed selectively.
