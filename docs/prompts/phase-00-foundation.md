# Phase 0 — Foundation

You are working on Movie Match. Read `CLAUDE.md` first; it is binding.

## Before you start

Read, in this order:
- `CLAUDE.md` — conventions and the list of things not to do
- `docs/TZ.md` sections 2 and 3 — scope and the trait vector
- `packages/shared/traits.json` — the 14 dimensions
- `docs/architecture.md`

Then check the current state of the repo yourself with `ls` and `git status` rather than
assuming what exists.

## Goal

Make the three parts of the repo runnable, verifiable and wired together, so that every
later phase adds features to a working system instead of building one.

## Build

1. **API bootstrap**
   - Confirm `uvicorn app.main:app` starts with no database configured and `/health`
     answers. It must not crash when `DATABASE_URL` is empty.
   - Add `app/services/` package with an `__init__.py` — business logic layer, empty for now.
   - Add `tests/conftest.py` with a FastAPI `TestClient` fixture and an async session
     fixture that uses an in-memory or throwaway database, skipped when no test DB is set.

2. **Database migrations**
   - Initialise Alembic in `services/api` (`alembic init migrations`), configured to read
     `DATABASE_URL` from `app.config`, not from `alembic.ini`.
   - Write the first migration from the models in `app/models.py`, including
     `CREATE EXTENSION IF NOT EXISTS vector`.
   - Add an `upgrade`/`downgrade` round-trip check to the test suite (skipped without a DB).

3. **Web bootstrap**
   - Confirm `npm run dev`, `npm run build`, `npm run lint`, `npm run typecheck` all work.
   - Add Vitest + React Testing Library. Add `"test": "vitest run"` to package.json.
   - Write one test for the existing `Home` page: it renders, and shows the error state
     when the API call fails.

4. **Shared contract check**
   - Write a test in `services/api/tests/test_contract.py` asserting that the trait keys in
     `packages/shared/traits.json` match `app.traits.TRAIT_KEYS` exactly, in order.
   - Write the mirror check in `apps/web`: a test that imports the same JSON file and
     asserts the key list is what the web code expects.

5. **Developer scripts**
   - Add a `Makefile` (or `tasks.ps1` for Windows) at the repo root with targets:
     `install`, `dev-api`, `dev-web`, `test`, `lint`. `test` runs the full gate below.

## Out of scope

No TMDB calls. No LLM calls. No authentication flows. No UI beyond what exists. Do not
add libraries beyond those listed in `pyproject.toml` and `package.json` without saying
why first.

## Required tests

These must all exist by the end of this phase:

- `tests/test_health.py` — `/health` returns 200; reports the trait count (already exists)
- `tests/test_traits.py` — vector round-trip, missing-key default, out-of-range rejection
  (already exists)
- `tests/test_contract.py` — JSON trait keys == Python trait keys, same order
- `tests/test_migrations.py` — upgrade then downgrade leaves no error (skip without DB)
- `apps/web/src/pages/Home.test.tsx` — renders; shows error state on failed fetch
- `apps/web/src/lib/traits.test.ts` — trait keys match the shared JSON

## Gate — do not skip

Run these and paste the real output:

```bash
cd services/api && ruff check . && ruff format --check . && pytest -q
cd apps/web && npm run lint && npm run typecheck && npm run build && npm test
```

Pass condition: **every command exits 0 and every test passes. No skips except the
DB-dependent ones, and say explicitly which were skipped and why.**

Manual checklist (do these yourself, report the result):
- [ ] `uvicorn app.main:app --reload` starts and `http://127.0.0.1:8000/docs` opens
- [ ] `npm run dev` opens and the page shows the green "connected" state with the API running
- [ ] The page shows the red error state with the API stopped
- [ ] `.env` is not tracked by git (`git status --porcelain` shows nothing for it)

## Report

Tell me:
1. The exact gate output.
2. Which tests you added and what each one would catch if it broke.
3. Anything in `CLAUDE.md` or `docs/TZ.md` that turned out to be wrong or unclear.
4. Do not start Phase 1.
