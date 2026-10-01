# ADR 0006 — The LLM provider sits behind an interface; which provider is open

Date: 2026-09-30 · Status: accepted (the interface) · **Open: the provider** ·
Amends: ADR 0004 (Gemini stays as the current implementation, no longer as a settled
choice) and the AI bullet of CLAUDE.md "Stack decisions" · Amended 2026-09-30 (below)

## Amendment, 2026-09-30: traits can run one film per request (`TRAIT_MODE=sync`)

**What happened.** With the user's new Gemini key:

- `models.list` worked (61 models; `gemini-3.5-flash-lite` and `gemini-embedding-2`
  present). That call works on any tier, so it proves the key, not billing.
- The user-approved 50-film batch (`docs/review-films.md`) was sent twice. Both times
  `batches.create` answered, in full:
  `400 FAILED_PRECONDITION {'error': {'code': 400, 'message': 'Precondition check failed.', 'status': 'FAILED_PRECONDITION'}}`.
  No job was created (`batches.list` empty), nothing was stored, nothing was charged.
- One ordinary `generate_content` call for one film (*Fight Club*), with exactly the
  batch request's prompt, JSON schema and settings, **worked**: 14 traits, valid JSON,
  370 input and 195 output tokens. Nothing was stored.

**Why not keep fighting batch.** The error carries no reason: no `details`, no project,
no "paid plan". The documentation points both ways: the
[API errors page](https://ai.google.dev/gemini-api/docs/api-errors) describes
FAILED_PRECONDITION as "a prerequisite is not met (for example, disabled billing)", while
the [pricing page](https://ai.google.dev/gemini-api/docs/pricing) lists Batch for
Flash-Lite as "Free of charge" on the free tier (read through a summariser; worth a look
by eye). Neither settles which prerequisite this account lacks, and finding out means
more paid attempts or account support. A path that works exists today.

**Decision.**

1. A fourth protocol, `TraitScorer.score(request) -> TraitAnswer`: one film, standard
   (not batch) API. Same prompt, same schema, same parsing, storage and attempt counting
   as batch. Gemini implements it with `generate_content` (`GeminiTraitScorer`).
2. `TRAIT_MODE` = `batch` (default, unchanged) | `sync`. **Batch is not removed:** if
   billing opens, setting `TRAIT_MODE=batch` is the way back, at half the price.
3. The provider translates its errors into three neutral ones: `RateLimited` (429, with
   the provider's retry hint), `TransientError` (5xx, timeout), `ProviderUnavailable`
   (billing, permission, authentication: the run stops, nothing more is sent). Any other
   refusal is one failed film, like a failed batch item.
4. Pacing and retries live in the pipeline, not the provider:
   `TRAIT_SYNC_REQUESTS_PER_MINUTE` (default 10, deliberately below free-tier limits,
   which differ per model and change) and `TRAIT_SYNC_RETRIES` (default 5; waits the
   provider's hint, else doubling, at most 120 s).
5. **Resumable.** Each film is committed as soon as it is answered. A run stopped by a
   daily quota or a refusal leaves the rest pending; running the same command again
   continues where it stopped (`select_pending` skips scored films). A film that was
   rate-limited past its retries is not counted as a failed attempt. A lost database
   connection is retried by `ingest.with_reconnect` (the ingestion's own reconnect, not a
   second one): a fresh session, the films still pending, the same run (added
   2026-10-01, after a 450-film run stopped at film 198 on `ConnectionDoesNotExistError`).
6. The run's cost line is written in `finally`, with `status=complete`, `stopped` or
   `interrupted` and the tokens used so far: the 2026-10-01 run that broke off wrote
   none, and its tokens are lost.

**Costs and trade-offs.**

- On a paid tier, sync costs the full standard rate, twice the batch rate
  (`TRAIT_SYNC_PRICING`, $0.30 / $2.50 per MTok); the dry run prints it. On the free
  tier it is not charged. `docs/costs.md` has both.
- Free-tier requests may be used by Google to improve its products (ADR 0004). Trait
  prompts carry only public film metadata; user data (explanations) is a separate
  decision and does not change here.
- This departs from CLAUDE.md "Use the Batch API for anything that is not user-facing";
  CLAUDE.md now names this exception.

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
