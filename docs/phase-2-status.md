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

The other two checklist items, exactly:

- **Match computed by hand: not done.** The formula is covered by a test,
  `test_match_is_recomputable_from_stored_numbers`, which recomputes an API match from the
  stored vectors and weights; it runs on every commit (CI).
- **5 explanations read against their reasons: not done.** About 20 explanations were
  generated and shown during the check, but none was checked item by item. Tests cover
  the input only: `test_the_prompt_carries_the_real_reasons` checks that the prompt
  carries the real shared traits. Whether the generated sentence describes them is not
  tested (that needs a person or an evaluation set).

Explanation cost, measured: 187 input / 29.6 output tokens on average over 19 runs, about
$0.00013 each at the standard rate; `docs/costs.md`.

Gate at closing: CI run https://github.com/smasheverybody99-hue/movie_match/actions/runs/36989348804
(`b28b9da`, green). `app/services/` coverage: the CI step
`coverage report --include="app/services/*" --fail-under=85` passed, so ≥ 85%. **The exact
figure was not read:** the run's log needs a GitHub login. It goes here after the next
full local run.

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

## Reasons repeated on every film — found and changed (2026-10-02)

The user noticed "Why you?" naming nearly the same three traits on every film
(visual style, emotional intensity, pace); 19 logged explanations confirmed it.

**Measured (read-only, 500 films with traits):** the two traits with the smallest spread
are also the highest on average — `emotional_intensity` mean 72.5, sd 14.3, 56% of films
between 70 and 85; `visual_style` mean 75.8, sd 14.3, 54%. For comparison `plot_twist`
30.9 / 20.4, `realism` 42.6 / 30.0. For the user's account, of 471 unrated films with a
match of 60% or more, the old rule (strength `w·min(taste, film)`) named
`emotional_intensity` in 93% and `visual_style` in 91%; the most common trio covered 48%.
Three causes stack: the old strength rewards a level every film has; the user's highest
weights are on exactly these two traits (weights measure consistency among favourites,
and a trait that barely varies looks consistent); the taste vector sits near the
catalogue mean (every trait within z −0.3…+0.9), the average of many varied films.

**Changed (user's choice, variant C):** a trait is a reason when the film stands out from
the catalogue mean (z ≥ 0.5) and the taste leans the same way (z ≥ 0); strength
`w·z_film` (TZ 1.12, FR-5; `matching.top_reasons`, `services/reasons.py`; thresholds
`reason_min_film_z`, `reason_min_taste_z`). Simulated on the same 471 films: no trait
above 28%, 105 different trios, the most common 7%, 14 films (3%) with no reason. The
explanation prompt now also gives the typical film's value per reason. The match
percentage (FR-5 formula) is unchanged. A stricter variant (taste also z ≥ 0.5) left 33%
of films without a reason and was rejected.

## Match spread for one user (2026-10-02, measurement only — no change decided)

Read-only, the user's account (32 ratings), every number from the stored vectors:

| Films | min | p10 | median | p90 | max |
|---|---|---|---|---|---|
| All 500 | 59 | 68 | 77 | 85 | 92 |
| Unrated (473) | 59 | 67 | 77 | 84 | 92 |
| Rated 8 or higher (13) | 75 | 77 | 86 | 89 | 92 |
| **Rated 5 or lower (12)** | 68 | 77 | **85** | 89 | 90 |

- **The 60% cut removes 2 of 473 unrated films** (0.4%). At 70%: 400 pass; 75%: 289;
  80%: 148; 85%: 44.
- **Films the user disliked score the same as films the user loved** (median 85 vs 86).
  For this user the percentage does not separate them.
- Sections as the API builds them: For you 85–92, Because you loved 85–88, Under 90
  minutes 75–82, **Outside your usual taste 81–86** — higher than Under 90 minutes and
  close to For you. Its retrieval (films 301–600 by embedding distance) found 173
  candidates, 1 under 60%. The section is "far in embedding space", not "lower match".

What the number tells the user today: nearly every film reads as a 70–85% match, so the
percentage ranks films but says little on its own. A separate decision (FR-5 formula),
not part of the reasons change.

## Recommendations skew old — measured (2026-10-13, tester feedback; no change applied)

A tester rated Interstellar, Oppenheimer, The Dark Knight, Whiplash and Gone Girl and was
offered Drunken Angel (1948), Lawrence of Arabia (1962), The Wages of Fear (1953), High
and Low (1963) and Pickpocket (1959).

**Measured** (read-only, one `READ ONLY` transaction against the main database, no LLM
call): those five films rated 9 today, the taste profile built by `taste.build_profile`
exactly as a real account would build it, then the "For you" section assembled exactly as
`recommend.add()` assembles it — ANN retrieve (300), floor cut, `score`, `shortlist`
(60), MMR with the director cap. Four of the tester's five films come back in the top 20,
so the account is reproduced closely enough to reason about.

| Stage | pre-1980 | Year median |
|---|---|---|
| Catalogue with traits (500) | **26%** | 1999 |
| ANN candidates, after the floor cut (265) | **26%** | 2001 |
| Best 50 by match | **34%** | 2000 |
| Shortlist for MMR (60) | 32% | 2002 |
| "For you", the 20 shown | **40%** | 2006 |

Three separate things, and only the middle one was suspected:

1. **Retrieval is neutral.** The candidate set has the catalogue's own decade mix (26%),
   so the embedding query is not reaching for old films.
2. **Trait match leans old**, 26% -> 34%. Those five inputs ask for high `realism`,
   `character_depth`, `plot_twist` and `emotional_intensity`, and mid-century world
   cinema scores high on exactly those. There is no year or quality term anywhere in the
   ranking to balance it: `movies.popularity` and `movies.tmdb_vote_count` are stored and
   never read when ranking.
3. **MMR makes it worse**, 32% -> 40% — the largest single step, and new information.
   Diversity is measured as embedding distance, and a 1948 Japanese film is about as far
   from a modern blockbuster as the catalogue gets, so diversification actively promotes
   the classics over a nearer modern film of the same match.

**The floor is the catalogue, not the ranking.** 26% of the scored 500 is pre-1980 by
design (`decade_quotas`, `docs/catalogue-500.md`: 132 of 500), so even a perfectly
neutral ranking puts one film in four on Home from before 1980. Only re-selecting the
catalogue moves that floor, and that voids the stage-1 manual review and pays for traits
again.

**What a tie-break would do** (measured on the same shortlist, applied nowhere). The term
goes into the MMR relevance, not into the match percentage, so FR-5 stays computable by
hand:

```
relevance = match / 100 - w * (1 - (year - 1920) / 106)
```

| w | pre-1980 | Year median | Dropped from the section |
|---|---|---|---|
| 0 (today) | 40% | 2006 | — |
| **0.02** | **30%** | 2009 | The Wages of Fear, Lawrence of Arabia |
| 0.05 | 15% | 2012 | + The Third Man, Psycho, The Tin Drum |
| 0.10 | 5% | 2014 | + Drunken Angel, The Godfather Part II |

`w = 0.02` brings the section back to roughly the catalogue's own mix at the cost of two
films; 0.10 all but empties it of anything old. The decision (whether, and at what
weight) is open — TZ backlog, 2026-10-13.

**Popularity is not the problem.** The section's popularity median is 21.9 against the
catalogue's 19.6, and a 2026 film with popularity 82.4 sits at place 6 while place 1 is a
1963 film with 11.1: the ranking is indifferent to popularity, not biased by it. Note
`architecture.md`'s re-rank step names "popularity damping", which was never built and
points the other way (holding blockbusters back); what the measurement supports is a
recency term, so building one is not the same as building that.

**Also seen, separately:** obscure brand-new films score high — Disclosure Day (2026,
place 6) and Elize: Shadows of a Woman (2026, place 8). The 2020s quota (62 films) is
filled by TMDB popularity, which on recent years means whatever is trending, so a
recency term alone would promote these. A quality floor (`tmdb_vote_count`, median 4,072
in the catalogue) is the lever for that, and is a separate decision.

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
