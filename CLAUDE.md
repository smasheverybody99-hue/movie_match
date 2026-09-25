# Movie Match — project instructions for Claude

AI-powered movie discovery. Two clients (React web, Flutter mobile) on one Python API.
Read this file before touching code. If something here conflicts with a request, say so instead of silently picking one.

## Where the requirements live

- `docs/TZ.md` — the specification. What gets built, and the acceptance criteria for each
  requirement. If a request conflicts with it, say so instead of guessing.
- `docs/prompts/phase-NN-*.md` — the phase you are working in. Each names the files to
  build, the tests that must exist, and a gate that must pass before the next phase.
- `docs/ui.md` — the design system and screen specs.

Work only within the current phase. A good idea that belongs to a later phase goes into
the backlog in `docs/TZ.md` section 2, not into this commit.

## Repo layout

```
apps/web         React 19 + Vite + TypeScript
apps/mobile      Flutter 3.47 / Dart
services/api     Python 3.12 + FastAPI + SQLAlchemy 2 (async)
packages/shared  Cross-language contracts (traits.json). Single source of truth.
docs/            Architecture notes and decision records
```

## The one thing that matters

Every feature in this product rests on **trait vectors**: each movie is scored 0-100 on the
14 dimensions in `packages/shared/traits.json`. Taste profiles, "Movie DNA", match
percentages and Character Match are all derived from them.

Rules:
- Never invent a new trait name inline. Add it to `packages/shared/traits.json` first,
  then mirror it in `services/api/app/traits.py`, then migrate the data.
- Trait order in the vector is the order in that file. Do not reorder.
- A match percentage must be computable by hand from stored numbers. No opaque scoring.

## Stack decisions (settled — do not re-litigate without a new ADR in docs/decisions/)

- **DB**: PostgreSQL via Supabase, `pgvector` for embeddings, HNSW index.
- **Auth**: Supabase Auth. The API verifies the Supabase JWT; it never issues its own.
- **AI**: Claude Haiku 4.5 for bulk trait extraction (Batch API) and cached "why you'll
  like this" text. Claude Sonnet 5 only for the conversational assistant.
- **Movie data**: TMDB. Commercial licence required before public launch — see docs/legal.md.

## Conventions

Python (`services/api`)
- Python 3.12, `ruff` for lint+format, `mypy` in non-strict mode, line length 100.
- Async everywhere: `async def` endpoints, `AsyncSession`, `asyncpg`. No sync DB calls.
- Layers: `routers/` (HTTP only) -> `services/` (logic) -> `models.py` (SQLAlchemy).
  A router never builds a SQL query directly.
- Pydantic v2 schemas in `schemas.py`. Request models end in `In`, responses in `Out`.
- Settings only through `app/config.py`. Never read `os.environ` elsewhere.

TypeScript (`apps/web`)
- Strict mode on. No `any` — use `unknown` and narrow.
- Server state through TanStack Query only. No fetch calls inside components.
- API types live in `src/lib/types.ts` and mirror the API's Pydantic schemas by hand.
  When a schema changes, change both in the same commit.
- Styling with CSS variables from `src/styles/tokens.css`. No inline hex colours.

Dart (`apps/mobile`)
- Riverpod for state, Dio for HTTP, go_router for navigation.
- Colours come from `lib/theme/tokens.dart`, which mirrors the web tokens exactly.

## Testing

Test layout:

```
services/api/tests/*.py           phase-0 suites: health, traits, contract, migrations
services/api/tests/unit/          from phase 1: formulas, parsing — no DB, no network
services/api/tests/integration/   from phase 1: endpoints against a test database
apps/web/src/**/*.test.tsx        component states
apps/mobile/test/                 widget states
```

The four phase-0 suites stay where they are; do not move them. New API tests from
phase 1 onward go into `unit/` or `integration/`.

Database-backed tests use the `db_session` fixture and skip themselves unless
`TEST_DATABASE_URL` is set. There is no SQLite fallback: the schema uses pgvector and
JSONB, so a SQLite run would be testing a different database than the one we ship.

Rules:

- Coverage of `app/services/` and `app/pipelines/` stays at or above 80%.
- No test calls a real external API. Record fixtures instead.
- Every endpoint has a test for: missing auth, forged token, invalid input, not found.
- Every screen has a test for each of its four states: loading, empty, error, content.
- A phase is not finished until its prompt's required-test list is fully written.

- Every API endpoint gets at least one test in `services/api/tests/`.
- Recommendation logic gets unit tests with hand-written fixtures, not live DB data.
- Run before any commit: `ruff check . && pytest` in `services/api`,
  `npm run lint && npm run build` in `apps/web`.

## Do not

- Do not write TMDB API keys, Supabase service keys or Anthropic keys into any file.
  They live in `.env` only, and `.env` is gitignored.
- Do not fetch from TMDB inside a request handler. Ingestion is a background job.
- Do not call an LLM inside a request handler without a cache lookup first.
- Do not add a feature that is not in the current phase of docs/roadmap.md.
  Write it into the backlog section instead.
- Do not use character images, logos or artwork anywhere in Character Match. Text names
  only, with the disclaimer. See docs/legal.md.

## Commit style

`area: short imperative summary` — e.g. `api: add rating endpoint`, `web: movie DNA page`.
One logical change per commit.
