# Phase 5 — status

Last updated: 2026-11-17 · Phase: **5 (closed alpha), code on branch `f5-alpha`, not
merged** · Phase 4 is not closed yet: it waits for the Lighthouse numbers (F3 item 5)

Phase prompt: `docs/prompts/phase-05-alpha.md`. The user decided on 2026-11-17 to start the
code now, without waiting for Lighthouse: the two do not depend on each other. **The branch is not merged
into `main` before F4 closes**, and the merge and migration `0006` on the main database
each need the user's own approval. No paid request was made for this phase.

## Decisions (user, 2026-11-17: every recommendation accepted)

| Question | Decision | Where |
|---|---|---|
| "Watched" | A `marked_watched` **or** a `rated` for the film; the report gives both, and each on its own | `app/pipelines/metrics.py` |
| "Shown" | At least half of the card in view for 1 s; a (user, film) pair counts once, at its first showing | `apps/web/src/lib/telemetry.ts`, `metrics.py` |
| Where events are written | The server, in the action's own transaction: `rated`, `added_to_watchlist`, `marked_watched`, `assistant_query`, `onboarding_done`. The client: `recommendation_shown`, `recommendation_clicked`, `onboarding_step` | `app/services/events.py` |
| D1 / D7 | Any event in the 24 h starting 1 (7) days after the user's `created_at` | `metrics.py` |
| Who is counted | Only users with `users.alpha_tester` set (one SQL update for the 12) | migration `0006`, `metrics.py` |
| The data notice | Once after sign-in, before any screen; accepted on the server; declining signs out; a one-line reminder on the assistant | `components/DataNotice.tsx`, ADR 0004 exception |
| "Not right?" reason | Four chips (Ko'rganman / Janrim emas / Juda eski / Boshqa), or none; no free text. On Home cards, the hero and the assistant's cards. The card leaves the current view only; ranking is not changed (TZ 1.31) | `components/NotRight.tsx`, `POST /feedback` |
| NSFW | Hidden from every list (search, onboarding, recommendations, the assistant); the film page warns, without images, until the viewer chooses. Signal: Google's `PROHIBITED_CONTENT` refusals + the hand list (Baise-moi, Caligula, Irreversible); TMDB's age rating after the alpha | `app/pipelines/sensitive.py` |
| The explanation limit | "Bugungi izohlar tugadi — ertaga yangilanadi" (en, ru as accepted), under the template sentence on the film page | `MoviePage.tsx`, the i18n test |
| Migration `0006` on the main database | `alembic upgrade 0005:head --sql`, one transaction, `lock_timeout`, as with `0005` — when the user approves | below |

## Built

API (`services/api`):
- Migration `0006`: tables `events` and `recommendation_feedback`; `users.alpha_tester`,
  `users.data_notice_accepted_at`, `movies.sensitive`. Additive only: today's live code runs
  unchanged on the new schema.
- `POST /events`: batches of up to 50, one transaction; one malformed event (wrong type,
  missing film or source, unknown field, a film not in the catalogue, a time more than 7
  days old or 5 minutes ahead) rejects the whole batch with 422.
- The server's own events, written with their actions: ratings, the watchlist, the
  assistant's claim of a message (never the question), and `POST /onboarding/done` (also sets
  `users.onboarded_at`, which nothing set before; only the first call records).
- `POST /feedback`: "this recommendation was wrong", one row per user and film.
- `GET /me` now says `data_notice_required` (setting `DATA_NOTICE_REQUIRED`, default
  true) and `data_notice_accepted_at`; `POST /me/data-notice` accepts, once.
- `GET /movies/{id}` says `sensitive`; the four list queries leave sensitive films out.
- `python -m app.pipelines.metrics --from --to [--as-of] [--all-users]`: read-only; prints
  the five metrics, shares with a 95% Wilson interval, and the "wrong" presses by reason.
- `python -m app.pipelines.sensitive [--apply] [--skip ids]`: lists, then marks.

Web (`apps/web`):
- `lib/telemetry.ts`: a queue sent every 10 s, at 20 events, or with `keepalive` when the
  page is hidden; a failed batch is retried, a refused one is dropped with a warning;
  nothing is sent signed out; a new account starts with an empty queue.
- Home rows, the hero and the assistant's cards report showings and clicks; onboarding
  reports its steps and calls `/onboarding/done`.
- "Not right?" under those cards; the data notice gate; the sensitive-film page; the
  explanation-limit line.

## Gate

| | Result |
|---|---|
| Local, API (2026-11-17, no test database) | `ruff check` 0, `ruff format --check` 0, `mypy app` 0, `pytest` **420 passed, 320 skipped**. The skipped tests need `TEST_DATABASE_URL` (the Frankfurt test project is paused): every database test of this phase runs only in CI |
| Local, web (2026-11-17) | `eslint` 0, `tsc` 0, `vitest` **375 / 375** (31 files), `vite build` 0 |
| CI, branch `f5-alpha` | see `docs/STATUS.md` (filled in from the run) |

Required tests, all present:
- `tests/integration/test_events.py`: each type with its shape, a batch in one commit,
  one malformed event rejects the batch, the server's events with their actions, none
  for a failed action.
- `tests/unit/test_metrics.py`: a hand-made alpha (`tests/metrics_dataset.py`), every number
  worked out in a comment; `tests/integration/test_metrics_store.py` reads it back from
  the database.
- `tests/integration/test_events_privacy.py`: a typed phrase through every path that makes
  an event; no column of any event holds it; the table has no free-text column.

Also: `test_events_check.py` (unit), `test_feedback_api.py`, `test_data_notice_api.py`,
`test_sensitive.py`, `test_sensitive_list.py`; `test_auth.py` lists the four new routes;
`test_account_deletion.py` covers `recommendation_feedback`. Web: `telemetry.test.tsx`,
`NotRight.test.tsx` (closed, open, sent, failed), `DataNotice.test.tsx` (loading, notice,
accepted, declined, failed, not needed, error), `MoviePage.test.tsx` (sensitive, limit line),
the wording of the chips, the notice and the limit line in `i18n.test.tsx`.

## Needs the user

1. **Merge into `main`**: only after F4 closes, and only with the user's approval.
2. **Migration `0006` on the main database**: with approval. It only adds, so it can go
   **before** the merge. The deployed code must never run ahead of the schema: `Movie.sensitive`
   is in every film query.
   `alembic upgrade 0005:head --sql` → read → run in one transaction with `SET LOCAL
   lock_timeout = '5s'`.
3. **The sensitive list, before `--apply`**: the dry run lists what it would mark. Google's
   refusals in the 500-film selection include films that are not explicit: Oldboy (670),
   Young Hearts (2024, 1232449), Hope (2013, 255709), My Fault (1010581). They have no
   traits, so they are in no recommendation today, but they would leave search. The user
   says which to `--skip`. The command writes to the main database: run it only with the user's yes.
4. **The 12 testers**: their user ids after they sign in, then one `UPDATE users SET
   alpha_tester = true WHERE id IN (...)`, with approval.
5. **Live check after deploy**: the notice on a fresh account, "Not right?" on Home and in
   the assistant, a sensitive film's page by link, the limit line, and the events arriving
   (`python -m app.pipelines.metrics --all-users` for the day).

## Known limits

- The notice is enforced by the client: the API does not refuse the assistant or an
  explanation to a user who has not accepted. There is one client, and every screen behind
  sign-in waits for the notice.
- A repeated watchlist add or re-rating writes another event; the metrics take the first
  per user and film.
- "Shown" needs IntersectionObserver; without it nothing is recorded rather than everything.
- D1 / D7 start from `users.created_at`, the first request after sign-in.
