# ADR 0006 — The LLM provider sits behind an interface; which provider is open

Date: 2026-09-30 · Status: accepted (the interface) · **Open: the provider** ·
Amends: ADR 0004 (Gemini stays as the current implementation, no longer as a settled
choice) and the AI bullet of CLAUDE.md "Stack decisions"

## Context

ADR 0004 put trait extraction, embeddings and explanations on Gemini. No paid Gemini
run has happened: the first submit was refused with `400 FAILED_PRECONDITION`, and turning
billing on requires Google Cloud's $50 card hold, which the user has not accepted. An
alternative is not chosen yet.

Until 2026-09-30 the Gemini SDK was imported by the trait pipeline, the embeddings
pipeline and the explanation service, each with its own prices and its own way of counting
tokens. A switch would have touched all three, and the embedding size (1,536) was a
constant tied to one model's options.

## Decision

1. **Three protocols in `app/providers/base.py`**, in product terms, naming no vendor:
   - `TraitExtractor.submit(requests) -> job id`, `.collect(job id) -> TraitBatchResult`
   - `Embedder.embed(texts) -> Embedded(vectors, usage)`, with `dim`
   - `Explainer.generate(system, prompt) -> Generated(text, usage)`

   Prompts, the JSON contract, parsing, storage, caching, attempt counting and daily caps
   stay in the pipelines and services. A provider only carries text and vectors.
2. **`LLM_PROVIDER` setting** (default `gemini`, the only value today). Adding a provider
   is one module in `app/providers/` and one line in `PROVIDERS`
   (`app/providers/__init__.py`), plus its API key in `app/config.py`.
3. **Gemini moves behind the interface unchanged** (`app/providers/gemini.py`): same
   models, prompts, thinking settings and prices as ADR 0004. Building it needs no key, so
   `--dry-run` can read prices without credentials. The first real call still stops with
   "GEMINI_API_KEY is not configured".
4. **`EMBEDDING_DIM` is a setting** (default 1536). Providers differ (1,024, 1,536 and
   3,072 are common), and pgvector stores the size in the column type. The API at start-up
   and the embeddings pipeline before any run — dry run included — compare it with
   `movie_embeddings.embedding` and stop with an explicit error on a mismatch
   (`app/schema_checks.py`). A provider whose embedder cannot produce the size refuses to
   build (`UnsupportedDimension`). Nothing adapts silently.
5. **One usage and cost measure for every provider.** Each call reports `Usage` (requests,
   input tokens, output tokens with thinking included, and whether the count is estimated
   from characters because the provider reported none). Each provider states its
   `Pricing` with a source. Every run — a collected trait batch, an embedding run, one
   explanation — writes one line to the `app.cost` logger:

   ```
   run=traits provider=gemini model=gemini-3.5-flash-lite requests=50 input_tokens=21000
   output_tokens=12500 usd=0.0188 tokens=reported pricing="..."
   ```

## Consequences

- Choosing the provider later is a new module and a settings change, not a refactor.
- **If the chosen provider's embeddings are not 1,536-d**, the switch needs a migration:
  re-create `movie_embeddings.embedding` at the new size with its HNSW index, and embed
  every film again (stored vectors cannot be converted). Above 2,000 dimensions pgvector's
  HNSW needs `halfvec`. The start-up check makes forgetting this impossible to miss.
- Test fakes implement the protocols directly (`tests/unit/test_providers.py`); the
  Gemini wire format keeps its own tests over a fake SDK.
- Prices now live next to each provider's code; `docs/costs.md` compares candidates.

## Still open

Which provider. Candidates and their prices are in `docs/costs.md`. The choice needs: a
batch mode (half price) for traits, an embeddings API, no training on submitted content
on the tier we pay for, and a billing set-up the user accepts.
