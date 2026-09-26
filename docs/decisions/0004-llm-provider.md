# ADR 0004 — LLM provider for trait extraction and embeddings: Gemini

Date: 2026-09-26 · Status: accepted · Supersedes: the AI bullet of CLAUDE.md "Stack
decisions" (for bulk trait extraction only) · Resolves: ADR 0003

## Context

The Phase 1 plan needed two new vendor accounts: Anthropic (Claude Haiku 4.5, Batch API,
for the 14-dimension trait vectors) and a second one for embeddings, because Anthropic has
no embeddings API (ADR 0003 left that choice open). Google's Gemini API offers both a
batch text-generation API and an embeddings API under one account and one key.

The reason for the switch is the account count, not the price. The estimated saving is
real but modest (below).

### What this supersedes

- **ADR 0001** makes no AI-provider decision (stack: FastAPI, React, Flutter, Supabase),
  so nothing in it changes.
- **CLAUDE.md, "Stack decisions" — AI:** "Claude Haiku 4.5 for bulk trait extraction
  (Batch API)" is replaced by Gemini for that job. The rest of that bullet is **not**
  changed by this ADR: Haiku for the cached "why you'll like this" text and Sonnet 5 for
  the conversational assistant stay as written. CLAUDE.md's cost section still says
  "Claude Haiku for bulk work"; it should be updated to match (see Follow-ups).
- **ADR 0003:** resolved by this ADR. Its Voyage / OpenAI / local options are not taken.

## Decision

| Job | Provider and model | How |
|---|---|---|
| Trait extraction | Gemini `gemini-3.5-flash-lite` | Batch API, **paid tier**, `thinking_level=MINIMAL`, JSON-schema response |
| Embeddings | Gemini `gemini-embedding-2` at **1,536 dimensions** | `embed_content`, standard API, **paid tier**, one request per film |

Both sit behind the seams that already existed (`BatchesClient` protocol in
`app/pipelines/traits.py`, `Embedder` protocol in `app/pipelines/embeddings.py`); the
client is built in one place, `app/pipelines/gemini.py`. Settings: `GEMINI_API_KEY`.

The seam held. Provider-specific code is confined to `build_request`, `submit`,
`read_item` and `collect` in the trait module, plus the new `GeminiEmbedder`. The
prompt, `parse_response`, validation, storage, retry-once-then-fail logic and the
`--dry-run` / `--yes` / `--limit` / `--ids` CLI are unchanged.

### Why `gemini-3.5-flash-lite`

The cheapest model that is not the oldest one, and the same staged discipline as before
decides whether it is good enough: the 50-film hand review (stage 1) is the test, with the
same pass rule (no more than 5 of 50 clearly wrong). If it fails, the next step is
`gemini-3.8-flash`, not a bigger run. Changing model means editing `MODEL` and the two
rate constants in `traits.py`.

### Why paid tier only

Google's Gemini API Additional Terms differ by tier (fetched 2026-09-26):

- **Unpaid services** (including the unpaid quota of the Gemini API): "Google uses the
  content you submit to the Services and any generated responses to provide, improve, and
  develop Google products and services." "Human reviewers may read, annotate, and process
  your API input and output." "Do not submit sensitive, confidential, or personal
  information to the Unpaid Services."
- **Paid services** (a project with an active Cloud Billing account): Google "doesn't use
  your prompts (including associated system instructions, cached content, and files such as
  images, videos, or documents) or responses to improve our products." Prompts and
  responses are still logged "for a limited period of time, solely for detecting and
  preventing violations of the Prohibited Use Policy … and any required legal or regulatory
  disclosures."
- In the EEA, Switzerland and the UK the paid-service terms apply to every tier.

For Phase 1 the payload is public TMDB metadata plus our own scores, so the free tier
would not leak anything sensitive; the reasons for paid are the rate limits (a 5,000-film
run must not be stretched) and the precedent. The precedent matters from Phase 4, when
user queries and taste data go through the API: **anything containing user data must run
on a paid-tier key.** Enabling billing is the user's action; the agent never adds a payment
method (CLAUDE.md).

## Embedding dimensions

`gemini-embedding-2` returns **3,072 dimensions by default** and supports 128–3,072
(Matryoshka truncation; the API normalises truncated vectors, and recommends 768, 1,536 or
3,072). pgvector's HNSW index on the `vector` type stops at 2,000 dimensions, so 3,072 does
not fit. We request **1,536**: it equals the existing `EMBEDDING_DIM` and column, so
**no migration is needed**. `embed_films` still rejects any vector that is not 1,536-d.

Behaviour that differs from the assumptions in ADR 0003:

- A request with several inputs returns **one aggregated embedding**, not one per input.
  The embedder therefore sends one request per film, a few at a time, and rejects any
  response that is not exactly one vector.
- The model takes no `task_type`; the documented document format `title: … | text: …` is
  used (`title: none | text: <embedding text>`). Queries (Phase 4) will need the documented
  query form, `task: search result | query: …`.
- Uzbek: the model is documented as multilingual ("over 100 languages"); Uzbek is not
  named. ADR 0003's rule stands: test 20 real Uzbek queries before Phase 4 commits.

The embeddings Batch API (half price) is **not** used, although CLAUDE.md prefers the
Batch API for non-user-facing work: it saves about $0.10 per 5,000 films, needs a second
polling loop, and its Tier 1 enqueued limit (500,000 tokens) is below the catalogue's
~1.04M tokens. Revisit if the catalogue grows to 20,000+.

## Cost (estimates; a staged run measures the real numbers)

Input tokens come from real prompt lengths (~3.5 characters per token), output is assumed
at 250 tokens per film. Paid-tier Batch rates checked 2026-09-26.

| Films | `gemini-3.5-flash-lite` ($0.15 in / $1.25 out) — chosen | `gemini-3.8-flash` ($0.375 / $1.875) | `gemini-3.1-flash-lite` ($0.125 / $0.75) |
|---:|---:|---:|---:|
| 50 (review list) | **$0.02** | $0.03 | $0.01 |
| 500 | **$0.19** | $0.31 | $0.12 |
| 5,000 | **$1.87** | $3.11 | $1.19 |

Embeddings, 5,000 films: ~1.04M tokens (film text with a typical trait summary and the
document prefix) × $0.20 per million = **$0.21**.

Whole catalogue, traits + embeddings: **~$2.08**, against ~$4.2–4.3 in the previous plan
(Haiku $4.15–4.22, plus $0.02–0.11 for embeddings).

Output is ~83% of the trait cost. If answers, including any thinking tokens, run twice as
long (500 tokens per film), the 5,000-film run is ~$3.43 on the chosen model. Thinking
tokens are billed as output and count against `max_output_tokens`; the collector sums them
into the measured cost.

## Risks and what is unverified

- **Nothing has run against the live API.** The request shape is validated against the
  SDK's own types (`InlinedRequest`, `InlinedResponse`, `BatchJob`); whether the service
  accepts `thinking_level=MINIMAL` on this model, and the `minimum`/`maximum` keywords in
  the response schema, is only known once stage 1 runs. A rejection is per request, is
  recorded as a failure, and costs pennies.
- **Quality is unverified.** Trait scores from this model have not been read by a person.
  The stage 1 hand review decides.
- **Refusals.** Gemini can refuse an adult-content film (`finish_reason SAFETY`,
  `PROHIBITED_CONTENT`, or a blocked prompt). Such a film is recorded in `trait_failures`
  with the reason and never stored with default scores. The review list includes 365 Days.
- **Prices move.** Google's pages were read on 2026-09-26; `gemini-3.8-flash` input/output
  prices are stated "through 12/31/26". Re-check before stage 3.
- **The Anthropic account is still needed later.** Phase 2+ explanations and the Phase 4
  assistant remain on Claude per CLAUDE.md, so the "one fewer account" benefit holds for
  Phase 1 only, unless those are moved too. That is a separate decision.

## Consequences

- `google-genai` replaces `anthropic` in `pyproject.toml`; re-add `anthropic` when the
  assistant is built.
- `.env`: `GEMINI_API_KEY` (paid-tier project). `ANTHROPIC_API_KEY` is kept for later phases
  and unused by the data pipelines.
- `trait_batches.id` now holds a Gemini job name (`batches/…`), and `status` gains
  `failed | cancelled | expired`. No migration: the column sizes already fit.
- A job that ends without results leaves its films pending and does not count an attempt.
- `movie_traits.model` records `gemini-3.5-flash-lite`; `movie_embeddings.model` records
  `gemini-embedding-2`, so a later model switch can re-score or re-embed selectively.

## Follow-ups (not done here)

- Update CLAUDE.md (Stack decisions, "Keep the running cost down"), `docs/architecture.md`
  and `README.md`, which still say Haiku for bulk trait extraction.
- Rerun the stage plan: 50 films, hand review, then 500, then all, asking before each step.
