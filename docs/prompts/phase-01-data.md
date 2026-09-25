# Phase 1 — Data foundation and Movie DNA

Read `CLAUDE.md` first. Phase 0's gate must be green before you start; check it.

## Before you start

Read:
- `docs/TZ.md` sections 3 and 4 (FR-2)
- `packages/shared/traits.json`
- `app/pipelines/tmdb.py` and `app/pipelines/traits.py` — the skeletons to finish
- `docs/legal.md` — TMDB attribution and licensing constraints

## Goal

A database of at least 20,000 films where every film has a validated 14-dimension trait
vector and an embedding, and similarity search returns sensible neighbours.

This phase produces the asset the whole product rests on. Correctness matters more than
speed here.

## Build

1. **Ingestion job** — `app/pipelines/ingest.py`
   - Fetch films from TMDB above a popularity threshold, with credits and keywords.
   - Resumable: a run that dies at film 12,000 continues from there, not from zero.
   - Respect rate limits with backoff. Never hammer on 429.
   - Upsert, never duplicate. Re-running is safe.
   - Write a `sync_runs` table recording start, end, counts and last processed id.

2. **Trait extraction** — finish `app/pipelines/traits.py`
   - Submit batches through the Anthropic Batch API using Claude Haiku.
   - Batch size from `settings.trait_batch_size`.
   - Validate every response with `parse_response`; a malformed response is retried once,
     then recorded as failed — never written with default values.
   - Store both the JSONB scores and the pgvector column, plus the model name and
     `spec_version`.
   - A `--dry-run` flag prints the prompt and estimated cost without calling the API.

3. **Embeddings** — `app/pipelines/embeddings.py`
   - Build the embedding text from title, overview, genres, keywords and the trait summary.
   - Store in `movie_embeddings`. Create the HNSW index in a migration.

4. **Similarity service** — `app/services/similarity.py`
   - `find_similar(movie_id, limit, filters)` using pgvector ANN.
   - Hard filters: year range, runtime, language, max violence.
   - Returns candidates with their trait vectors attached, ready for ranking in Phase 2.

5. **Quality report** — `app/pipelines/report.py`
   - A command that prints, for a given list of film ids, their trait scores in a table.
   - You will use this for the manual review below.

## Out of scope

No recommendation logic (that is Phase 2). No user-facing endpoints. No UI.

## Required tests

- `tests/unit/test_ingest_mapping.py` — a recorded TMDB payload maps to the right model
  fields; missing optional fields do not crash
- `tests/unit/test_ingest_resume.py` — given a `sync_runs` row, the job resumes from the
  recorded position
- `tests/unit/test_trait_prompt.py` — the prompt contains every trait key and the film's
  actual data
- `tests/unit/test_trait_parsing.py` — valid response parses; missing key raises;
  out-of-range raises; extra keys are ignored; non-JSON raises
- `tests/unit/test_embedding_text.py` — the embedding text is deterministic for the same
  input and includes the fields it should
- `tests/integration/test_similarity.py` — with seeded fixture films, `find_similar`
  returns the expected neighbour order and respects each filter
- `tests/integration/test_upsert_idempotent.py` — ingesting the same film twice leaves one
  row with the newer data

Use recorded fixtures for TMDB and Anthropic responses. **No test may call a real API.**

## Gate — do not skip

```bash
cd services/api && ruff check . && ruff format --check . && pytest -q --cov=app --cov-report=term-missing
```

Pass condition: **all tests pass and coverage of `app/pipelines/` and `app/services/` is
at least 80%.** Report the coverage number.

Manual checklist — this is the important one:
- [ ] Run the pipeline on 200 films. Report cost and time.
- [ ] Run `report.py` on 50 films you know well. Read the trait scores yourself.
      For each one, say whether the scores are right. **If more than 5 of 50 are clearly
      wrong, the trait prompt needs work — fix it and re-run before moving on.**
- [ ] Pick 5 films and check their nearest neighbours by eye. Do they make sense?
- [ ] Confirm every film in the database has both a trait vector and an embedding
      (report the count of films missing either — it must be 0).

## Report

1. Gate output and coverage number.
2. The 50-film review table and your verdict on it.
3. Measured cost per 1,000 films, extrapolated to the full catalogue.
4. Anything about the trait definitions that turned out not to work in practice.
5. Do not start Phase 2.
