# Phase 2 — status

Last updated: 2026-10-02 · Phase: **2 (recommendation engine and user API) — finished.**
Manual check passed (user, 2026-10-02); gate green (CI run 36989348804)

Phase prompt: `docs/prompts/phase-02-engine.md`. The prompt's precondition — Phase 1's
gate green *including the 50-film review* — is **not met**: Phase 1's code gate is green
but no film has traits or embeddings yet (`docs/phase-1-status.md`). The Phase 2 code was
built against hand-written fixtures in the meantime. Its manual checklist needs real data
and cannot be done until Phase 1 stages 1–3 have run.

## Decisions made in this phase

| Decision | Why | Where |
|---|---|---|
| **Match formula: TZ FR-5 (weighted distance)**, not the weighted cosine that `docs/architecture.md` gave (user, 2026-09-27) | On all-positive 0..100 vectors cosine rates nearly any two films 80–95% alike and ignores size (30-everywhere vs 90-everywhere scored 100%), so the 60% cut would remove almost nothing | `app/services/matching.py`; architecture.md and the phase prompt now point to FR-5 |
| Top reasons = `w·min(taste, film)`, only where both are ≥ 50 | "Neither of you likes romance" is not a reason; a film far above the user's level shares no more than the user wants | `matching.top_reasons` |
| MMR similarity = **embedding** cosine, over the best 3·k per section | With trait closeness, "far from what is picked" equals "far from the taste" (the top pick sits at the taste), so MMR could never displace a near-duplicate. Pairwise similarities are computed in SQL, so no 1,536-d vector crosses the network | `recommend.embedding_similarities` |
| Candidate query vector = weighted mean of liked films' unit embeddings, same weights as the taste vector | Retrieval by embeddings, ranking by traits (architecture.md) | `recommend.taste_embedding` |
| A film appears in one section only; sections fill in order For you → Because you loved → Under 90 → Outside your usual taste | Repeats across rows look sloppy | `recommend.recommend` |
| "Outside your usual taste" = films ranked 300–600 by embedding distance that still clear 60% | Different from what you usually rate, still a trait match | `recommend.retrieve(offset=…)` |
| Section titles are keys (`for_you`, …), not text | TZ §5: Uzbek and English from day one; no hard-coded strings | `SectionOut.key` |
| **Dismissals** table + `POST /dismissals`, `DELETE /dismissals/{id}` | FR-5 excludes dismissed films; nothing recorded a dismissal | migration `0004` |
| Explanations cached per **(user, film, language)** | A user who switches language would otherwise get the other language's cached text | migration `0004` adds `explanations.lang` to the primary key |
| `GET /recommendations` never calls the LLM; `GET /recommendations/{id}/explanation` does, cache first, on a miss only | FR-6: the screen never waits; CLAUDE.md: cache lookup before any LLM call in a handler | `app/services/explain.py`; architecture.md updated |
| `explanation_daily_calls_per_user = 20` | TZ §5: LLM cost < $0.20 per user per month. ~$0.0003 per explanation (standard API, not batch: a user is waiting) | `app/config.py` |
| `GET /onboarding/films` needs auth and leaves out rated films | FR-3: a user who comes back resumes where they stopped | `app/services/onboarding.py` |

## Built

Endpoints (all need a Supabase token): `GET/DELETE /me`, `POST/GET /ratings`,
`DELETE /ratings/{id}`, `GET/POST /watchlist`, `DELETE /watchlist/{id}`,
`POST /watchlist/{id}/watched`, `GET /recommendations?lang=`,
`GET /recommendations/{id}/explanation?lang=`, `POST /dismissals`,
`DELETE /dismissals/{id}`, `GET /onboarding/films`.

Services: `users`, `ratings`, `watchlist`, `dismissals`, `taste`, `matching`, `mmr`,
`recommend`, `explain`, `onboarding`. Migrations `0003` (ratings.updated_at) and `0004`
(dismissals, explanations.lang). Web types mirrored in `apps/web/src/lib/types.ts`.

Required tests, all written: unit `test_taste_vector`, `test_taste_weights`,
`test_matching` (hand arithmetic in comments), `test_top_reasons`, `test_mmr`; integration
`test_ratings_api`, `test_watchlist_api`, `test_recommendations`,
`test_explanations_cache`, `test_auth`, `test_isolation`, `test_account_deletion`. Also
`test_recommend_pick`, `test_explain`, `test_onboarding_interleave`, `test_dismissals_api`,
`test_me_api`, `test_onboarding_api`.

## Gate

**Not yet a single clean run.** ruff, `ruff format --check` and mypy pass; the web
types compile (`tsc --noEmit`). Every test file has passed at least once since the last
code change, run in pieces: unit + phase-0 suites 210 passed; `test_auth` +
`test_account_deletion` 54; dismissals, `/me`, onboarding, isolation 12; explanations 12;
recommendations 11; ratings, watchlist and the Phase 1 store suites 62 + 32 on rerun.

Every failure seen on 2026-09-27 was the network, not an assertion: `WinError 10054`
(connection reset by the Supabase pooler), then `getaddrinfo failed` (DNS). Round trips
were ~0.42 s, against ~170 ms during Phase 1. One full run was also stopped by Claude Code
for low memory.

Coverage of `app/services/`: **not measured yet**. Combining the interrupted runs gives
80% (the prompt asks for 85%), but those runs lost tests to dropped connections and the
clean reruns were not run with `--cov`, so that is a lower bound. Before committing, run
the gate once on a stable connection:
`ruff check . && ruff format --check . && pytest -q --cov=app --cov-report=term-missing`.

## Manual check — passed (user, 2026-10-02; real data, web app)

**Verdict (the user's words, summarised):** of the 20 films in "For you" the user would
watch almost all of them — the product's core claim holds. The other sections
("Because you loved X", "Under 90 minutes", "Outside your usual taste"): "not bad".
**F2 manual check: passed.**

The match checked by hand and the 5 explanations were not reported item by item; the
user's verdict covers the check as a whole. The match formula is also covered by
`test_match_is_recomputable_from_stored_numbers`.

Gate at closing: CI run https://github.com/smasheverybody99-hue/movie_match/actions/runs/36989348804
(`b28b9da`, green). `app/services/` coverage: the CI step
`coverage report --include="app/services/*" --fail-under=85` passed, so ≥ 85%; the exact
figure is in that run's log (needs a GitHub login to read, not read here).

Findings from the API log (the user's analysis):

1. **Explanations work.** About 20 `run=explanation` cost lines; the daily cap (20 per
   user) was reached, after which the film page showed the fallback text. Not a bug, but
   the user cannot tell the cap was hit: backlog item in TZ 1.9. The token numbers of
   these lines are in the user's terminal, not yet in `docs/costs.md`.
2. **Bug, fixed (`01d08f7`):** `POST /watchlist` answered **500** (`NotOnWatchlist:
   969681`). `add()` committed `INSERT … ON CONFLICT DO NOTHING` and then read the row
   with a separate SELECT; a `DELETE` from the same user in between (Save, then unsave)
   left nothing to read. Now one `INSERT … ON CONFLICT DO UPDATE … RETURNING`;
   `mark_watched` had the same window (read, then a separate UPDATE) and is now one
   `UPDATE … RETURNING` (a removed film is a clean 404). The new test reproduces the race
   and failed on the old code with the same `NotOnWatchlist`.
3. **Feed ~15 s at 45 ratings** from the dev machine: recorded in
   `docs/phase-3-status.md`; F5 (deploy) work, not touched now.

Still open: the verdict on the recommendations, the match checked by hand, 5
explanations read.

## Not done / open

1. **Manual checklist** (needs Phase 1 data): rate 30 films and judge the
   recommendations; verify one match by hand (automated too:
   `test_match_is_recomputable_from_stored_numbers`); read 5 explanations. The last one
   makes real Gemini calls (~$0.002 for 5) — ask first.
2. **Speed (TZ: recommendations < 500 ms) not measured.** A request is ~12 statements.
   From this machine each round trip to Supabase costs ~0.5 s today, so a request takes
   ~5 s here; server-side the ANN query takes ~1 ms. Needs measuring from a host next to
   the database.
3. **Popularity damping** (architecture.md re-rank step) is not implemented: the phase
   prompt does not list it. Ranking is match + MMR only.
4. **Account deletion** removes our rows, not the Supabase Auth identity (that needs the
   service key and belongs with the auth work). TZ FR-1 allows 30 days.
5. `GET /onboarding/films` is not in TZ §6's endpoint table, nor are `/me` (only
   `/me/dna`), `/dismissals` and the explanation endpoint. Add them to §6 when the TZ is
   next revised.
6. Cloud review (2026-09-27) ran on tracked files only, so it reported the untracked
   routers, services and migrations as missing. Its one valid finding — a new Gemini
   client on every request — is fixed (`deps._explainer`, cached per key).
7. `UserOut` in `schemas.py` is an unused Phase 0 placeholder; `MeOut` replaces it in
   practice.
