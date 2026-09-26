# Phase 1 — status

Last updated: 2026-09-25 · Phase: **1 (data foundation), paused before the first paid call**

Phase prompt: `docs/prompts/phase-01-data.md`. Adjustments for this run (from the user):
catalogue of 5,000 not 20,000 (TZ v1.2 now says the same); no LLM key yet, so stop before
any paid call; TMDB ingestion run for real.

## Where things stand

| Step | State |
|---|---|
| `.env` + Supabase connection | Done. Main and test projects reachable, Postgres 17.6, pgvector 0.8.2 |
| Migrations | Main DB at `0002 (head)`. Round-trip test passes on the test DB |
| TMDB ingestion (5,000 films) | **Done**, run 1 finished, 0 missing |
| Trait pipeline | Built and tested with fixtures. **Not run** — no Anthropic key yet |
| Embeddings | Built against a provider-neutral interface. **Provider not chosen** (ADR 0003) |
| Similarity service | Built, tested with hand-made vectors. Needs real embeddings to try by eye |
| Review report | Built. Review list in `docs/review-films.md` (draft) |
| Gate | Passes: ruff, format, 168 tests (0 skipped, real test DB). Coverage: `app/pipelines/` 81.6%, `app/services/` 100% |

## What was built

All in `services/api`:

- `app/pipelines/tmdb.py` — the only module that knows TMDB field names. Rate limiter
  (20 req/s), backoff that honours `Retry-After`, no retry on 404, text clipped to column
  sizes at this boundary.
- `app/pipelines/catalogue.py` — picks the catalogue: decade quotas, no language over 55%
  of a decade while others have candidates, most popular first inside that.
- `app/pipelines/ingest.py` — resumable ingestion. Plan and cursor live in `sync_runs`;
  25-film chunks written with one statement per table; reconnects and resumes after a
  dropped connection.
- `app/pipelines/traits.py` — Claude Haiku through the Batch API. `--dry-run` prints the
  prompt and cost without an API call; a paid run needs `--yes`; `--limit N` or `--ids`.
  A malformed answer gets one retry, then the film is recorded in `trait_failures` —
  never stored with default scores.
- `app/pipelines/embeddings.py` — embedding text builder and storage behind an
  `Embedder` protocol; refuses to run until a provider is chosen.
- `app/services/similarity.py` — `find_similar()` over pgvector cosine distance, filters
  for year, runtime, language and max violence; returns trait vectors for Phase 2.
- `app/pipelines/report.py` — trait table for the 50-film hand review.
- Migration `0002`: `keywords`, `movie_keywords`, `sync_runs`, `trait_batches`,
  `trait_failures`.
- Tests: `tests/unit/` (no DB, no network) and `tests/integration/` (real test DB). The
  TMDB fixture is a real recorded response; Anthropic results are validated against the
  SDK's own response types.

## The catalogue (measured in the database)

| | |
|---|---|
| Films | **5,000** (planned 5,000, missing 0, skipped 0) |
| Credits / people / keywords | 87,558 / 45,167 / 13,954 |
| Gaps | 83 films without keywords, 1 without overview, 1 without director |
| By decade | 1920s 63 · 1930s 125 · 1940s 188 · 1950s 250 · 1960s 312 · 1970s 375 · 1980s 500 · 1990s 687 · 2000s 875 · 2010s 1,000 · 2020s 625 |
| By language | 42 languages. en 2,877 (57.5%) · fr 569 · ja 442 · it 225 · es 170 · de 128 · cn 124 · ko 85 · zh 71 · sv 43 |
| Run time | 41 min wall clock, including three restarts |

English is above the 55% per-decade cap overall because the 1920s–40s pools had too few
non-English candidates; the fill-up rule then takes English films rather than leave the
quota short.

## Cost estimates (not yet measured)

Trait extraction, Claude Haiku 4.5, Batch API ($0.50 in / $2.50 out per million tokens):

| Stage | Films | Estimated cost |
|---|---|---|
| 1 — review list (`docs/review-films.md`) | 50 | **~$0.04** |
| 2 | 500 | **~$0.42** |
| 3 — full catalogue | 5,000 | **~$4.15–4.22** |

These are **estimates**: input tokens from real prompt length (~3.5 characters per
token), output assumed at 250 tokens per film. If answers run twice as long, the full
catalogue is ~$7. Stage 1 replaces the estimate with measured token counts.

Embeddings: ~940,000 tokens for all 5,000 films — cents, or free, at every hosted
option (ADR 0003).

## Bugs found during the real run, and the fixes

| # | What happened | Fix | Commit |
|---|---|---|---|
| 1 | Writing film by film would have spent ~2.4 h on network waits (~170 ms per round trip to Supabase) | One statement per table per 25-film chunk | `dedce7c` |
| 2 | Stopped at film 2,125: TMDB film 9473 has a 348-character character name (column holds 300). The failure could not even be recorded — the transaction was aborted | Text clipped to its column at the TMDB boundary; roll back before recording a failure | `421277f` |
| 3 | Network dropped at film 2,575 (`WinError 121`, then `ConnectionDoesNotExistError`) | Reconnect and resume from the saved cursor, up to 5 times; data errors still stop the run | `7a41a89` |
| 4 | The dropped connection left an orphaned session "idle in transaction" holding row locks; the next run timed out on them. The orphan was terminated by hand (`pg_terminate_backend`, nothing had been committed in it) | Job connections set `idle_in_transaction_session_timeout=60s` and `lock_timeout=20s`; lock waits are retried | `618cdcf` |
| 5 | A lock timeout exited instead of retrying: SQLAlchemy wraps asyncpg's error, so the class check missed it | Classify by SQLSTATE and the cause chain; tests build errors the way the driver raises them | `4f4e085` |

Found afterwards, while building the review list: the pipeline commands crashed printing
titles such as "Amélie" on a Windows console using code page 1251. Fixed — the commands
switch their output to UTF-8.

Also: `alembic.exe` is blocked on the dev machine (Smart App Control, most likely), so
migrations run as `python -m alembic upgrade head`. `tasks.ps1` / `tasks.sh` already do.

## Outstanding — needs a decision or a key

1. **Stage 1 not run.** Needs `ANTHROPIC_API_KEY` in `services/api/.env` and a yes for
   ~$0.04. Before that, edit `docs/review-films.md` so every film is one the reviewer
   knows well. Then, from `services/api`:
   ```
   python -m app.pipelines.traits submit --ids ../../docs/review-films.md --dry-run
   python -m app.pipelines.traits submit --ids ../../docs/review-films.md --yes
   python -m app.pipelines.traits collect <batch_id>      # when the batch has ended
   python -m app.pipelines.report ../../docs/review-films.md
   ```
   Pass rule: no more than 5 of the 50 clearly wrong. Then stage 2 (500), then stage 3
   — asking before each step up (CLAUDE.md).
2. **Embedding provider not chosen** — ADR 0003 lists the options. Needed before the
   embedding step and before the nearest-neighbour check by eye.
3. **Phase 1 manual checklist** still open: the 50-film review verdict, measured cost per
   1,000 films, neighbours for 5 films, and a 0 count of films missing traits or
   embeddings.
4. **Not built in this phase:** the daily TMDB re-sync that TZ FR-2 asks for (ingestion
   is resumable and idempotent, but nothing schedules it yet). Streaming providers were
   dropped from FR-2 in TZ v1.2.

## Housekeeping

- Everything up to `7cf3274` is pushed to GitHub (`origin/main`).
- `docs/TZ.md` v1.2 is committed.
