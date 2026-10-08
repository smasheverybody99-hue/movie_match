# Phase 3 — status

Last updated: 2026-10-02 · Phase: **3 (web application), code built, not finished** ·
On `main` since `66bc7a0` (2026-09-30)

Phase prompt: `docs/prompts/phase-03-web.md`. Its precondition — Phase 2's gate green
*including the verdict on the 30-rating test* — is **not met**: that test needs Phase 1
traits and embeddings, which do not exist yet. The user asked on 2026-09-29 to start
Phase 3 anyway; the conflict with `docs/STATUS.md` ("do not start F3 before the F2 manual
check") was raised in the session report. The web app was built against hand-written
fixtures and a dev-only mock API.

## Decisions made in this phase

| Decision | Why | Where |
|---|---|---|
| **Stay on Vite**, no Next.js | No guest mode, and the film page's top half is personal (match, "why you"): a crawler would index only TMDB's text. One static bundle, no Node server | `docs/decisions/0005-web-framework.md` (0002 was taken) |
| `GET /movies/{id}` has **optional auth**: with a token it adds the caller's match and reasons | TZ §6 marks it "ixtiyoriy"; the film page needs the match. A forged token is still 401 — optional means absent, not forged | `app/deps.optional_user_id`, `app/services/movies.py` |
| The film page, the watchlist and the feed use **one** match function on the same stored numbers | A film cannot show two different matches on two screens | `movies.personal_matches` (FR-5 via `matching.match_percentage`) |
| `GET /movies` filters: `year_from`, `year_to`, `max_runtime`, repeatable `trait=key:min` | Phase 3 search filters. The web's "strong in X" chip sends `min = 70` | `movies.search` |
| `GET /me/dna` (was in TZ §6, never built): taste vector by trait, rating count, average, top genre, `ratings_needed` | FR-7 screen | `movies.dna`, `routers/me.py` |
| `GET /onboarding/films?offset=` | "I haven't seen any of these" loads the next page without repeats | `services/onboarding.py` |
| Liked-aspect chips show for scores **above** 8.0 (8.0 itself: no chips) | FR-3, the design system and the phase prompt all say "above 8.0" | `components/RatingInput.tsx` |
| Onboarding progress in `localStorage`, **per user id**; ratings are saved to the API as they are given | FR-3 resume; two accounts in one browser must not share a half-done onboarding | `lib/onboardingStore.ts` |
| i18n: own 60-line module, `uz` default + `en`, typed keys; trait labels equal `traits.json` | No dependency for ~200 strings; the type makes a missing English string a build error | `src/i18n/` |
| Supabase Auth behind a 5-method `AuthClient` interface | Screens and tests never touch the SDK; tests pass a fake | `lib/supabase.ts`, `lib/auth.tsx` |
| Dev-only mock API (`VITE_MOCK_API=1`) | Walk every screen without Supabase keys or a scored catalogue. Imported only when `import.meta.env.DEV`; checked absent from `dist/` | `src/dev/mock.ts` |
| CI gate now runs `npm run typecheck`, `npm test` and the `": any"` grep | They are in this phase's gate; CI ran only lint and build for the web | `.github/workflows/gate.yml` |

## Built

Screens (each with skeleton, empty-with-action, error-with-retry and offline states):
Welcome (Google, Apple, email magic link) · Onboarding (pick → rate → done) · Home
feed · Film page · Search with filters · Watchlist with group chips · Movie DNA ·
Profile (language, sign out, delete account, TMDB attribution) · About (public).

Optimistic rating and watchlist changes, rolled back on failure (FR-4). Keyboard
rating: 1–9, 0 for 10 (design parity table). Offline banner; cached content stays on
screen; with nothing cached a screen says it is offline instead of spinning.

## Gate

Local, 2026-09-29, `apps/web`: `npm run lint` 0 problems · `npm run typecheck` 0 errors ·
`npm run build` OK (JS 363 KB, 112.6 KB gzip) · `npm test` **11 files, 90 tests, all
passed** · `grep -rn ": any" src/` nothing.

API: the new and changed integration suites (`test_movies_api`, `test_dna_api`,
`test_auth`, `test_onboarding_api`, `test_watchlist_api`) passed in CI with the whole
suite and the `app/services/` 85% coverage step (runs linked in `docs/STATUS.md`).
Locally only 29 of them finished within 10 minutes against the remote test database.

## Manual checklist

Done in headless Chrome (the installed Chrome, driven by puppeteer-core from
the job's temp folder; the Chrome extension was not connected), dev server in mock mode,
Uzbek UI.

| Item | Result |
|---|---|
| Onboarding as a brand-new user, timed (< 3 min) | **Not done.** Needs a person, working sign-in (Supabase keys) and scored films: `/onboarding/films` offers only films with traits, and none have traits yet |
| Every screen at 320px: nothing clipped, no horizontal scroll | 9 screens + the rating dialog: `scrollWidth = 320` on all. The first pass found watchlist titles cut to one letter; fixed (`9b046e1`) |
| Keyboard only | Tab walk on each screen at 1280px reached every visible control; the rating dialog traps Tab and closes on Escape |
| axe (axe-core 4, wcag2a/aa/21aa + best-practice) | **0 violations** on all 9 screens and the open rating dialog |
| Lighthouse, film page | Mobile (simulated throttling): **LCP 2.1 s**, TBT 720 ms, CLS 0.006. Desktop: LCP 0.6 s. **INP 80 ms** (timespan: open rating, press 9, save, save to watchlist). Caveat: Vite dev server (unminified React dev build) and no poster images — re-measure on a deployed production build with real posters |
| Feed speed with real data (2026-10-02) | **~15 s** for `GET /recommendations` at **45 ratings**, measured by the user during the F2 manual check: local API on the dev machine, main database in Singapore, real catalogue (500 films with traits). TZ asks < 500 ms. Phase 2 estimated ~5 s from this machine (~12 statements × ~0.5 s round trip); the measured time is three times that, cause not analysed. **Not touched now: F5 (deploy) work** — measure again from a host next to the database before deciding anything |
| API off, every screen | No white screen, no raw error text (checked for `Failed to fetch`, status codes, `{"detail"`); each screen shows what happened and a retry |

## Manual checklist, re-run with real data (2026-10-06)

After design v2 the screens changed, and the first run used mock data. This run: the
production build (`vite build` + `vite preview` on 5173), the real local API
(`uvicorn`, no `--reload`), the main database (Singapore, 500 films with traits), real
Supabase sign-in. Measurement only, with one exception decided by the user: onboarding
defect (a) below was fixed on 2026-10-08.

| Item | Who | Result |
|---|---|---|
| 1. Onboarding as a brand-new user, timed (< 3 min, TZ FR-3) | user | **3 min 10 s — over the 3 min target.** New account `+onb1`, the user's own pace, timer from the first onboarding screen to "done". A lower bound: the user designed the app, a real new user is slower. Of that, **58 s** was waiting for the 10 ratings to save (3.5–8.5 s each, median 6.4 s; API log). Two defects seen: (a) "See my recommendations" returned to the pick screen; (b) 5–6 s after each "Next". Diagnosis and decisions below. **FR-3 verdict deferred** to a re-run after deploy |
| 2. Every screen at 320px: nothing clipped, no horizontal scroll | Claude | **Pass.** 9 screens (Home, Search, Search "harry" — the longest real titles, e.g. "Harry Potter and the Deathly Hallows: Part 2" —, film page, Watchlist, DNA, Profile, About, 404) at 320 and 1440, English; 7 of them in Russian at 320 and 1440 (not the film page: its Russian explanation is not cached and would call the LLM). `scrollWidth` ≤ viewport everywhere, 0 overflowing elements, 0 clipped labels |
| 3. Keyboard only | user (by hand), 2026-10-08 | **Pass.** Feed, film page, rating dialog, search, watchlist, DNA, profile, with Tab / Shift+Tab / Enter / Space / Escape only: focus visible everywhere, logical order, dialogs close on Escape and keep focus inside while open. No defects |
| 4. axe 4.10.2, contrast and label violations zero | Claude | **Pass: 0 violations** on all of the above. One note: while Movie DNA loads (~3.5 s on this connection) its skeleton has no `h1` — axe `page-has-heading-one` (best practice) fires if run during loading; 0 once loaded |
| 5. Lighthouse, film page, production build | — | **Moved to after deploy** (decision 3 below): measured on the live URL, not localhost |
| 6. API off, every screen | user (by hand), 2026-10-08 | **Pass.** API stopped by Claude (port 8000 closed, no process left), production build still served. Feed, film page, search, watchlist, DNA, profile, each hard-reloaded (Ctrl+Shift+R): a plain message with "Try again" (e.g. "Couldn't load this film. Check your connection and try again."), no white screen, no raw error text, no endless spinner; the navigation keeps working. API restarted afterwards |

**Summary (2026-10-08): all six items run.** Passed: 2, 3, 4, 6. Item 1 was run (3:10) and its
defect (a) fixed; the FR-3 verdict waits for the re-timing after deploy. Item 5 (Lighthouse)
is measured on the live URL after deploy. Both are in `docs/STATUS.md`, "Keyingi qadam" 1.

How 2 and 4 were measured: in the user's Chrome (Claude in Chrome, main account, read
only — nothing clicked), each screen loaded in a same-origin iframe of the given width,
then `scrollWidth`, elements past the right edge, text wider than its box, and axe-core
4.10.2 inside the frame. The frame's scrollbar takes 15px, so 320 is measured as 305 —
stricter than a phone. Not covered yet: the onboarding screens and a watchlist with
items (the main account's watchlist is empty) — to be done on test accounts.

### Onboarding defects (2026-10-08) — diagnosis

**(a) "See my recommendations" → back to the pick screen. A bug, not the intended flow.**
`+onb1` had 10 ratings and a taste vector (database) when it happened, and the fresh
`/recommendations` answer was the full one. Cause: `Feed.tsx:127` redirects to
`/onboarding` when `ratings_needed >= 10`, and `QueryView` (`States.tsx:93`) renders
cached data even while it is being refetched. An earlier visit to `/` (09:41:33, 0 ratings)
had cached "10 needed"; ratings only mark it stale (`queries.ts:98`), the default cache
time is 5 min and only ~4.5 min had passed. `finish()` (`Onboarding.tsx:308`) navigated
to `/`, Feed showed the old answer at once and redirected, before the fresh request
(09:45:55 → 09:46:06, 11 s) returned. Progress had been cleared, so onboarding restarted
at "pick".

**(b) 5–6 s after "Next".** "Next" awaits `POST /ratings` (`Onboarding.tsx:226`); the
`GET /ratings` that follows is not waited on. Server time per rating, API log: 3.5–8.5 s,
median 6.4 s, of which the taste recompute's part 0.6–5.2 s. One rating is ~12 database
round trips in two transactions (`ensure_user` insert + commit; movie check, insert,
liked films with traits, user row, taste update, commit) plus a pool ping per checkout.
The work itself is small (10 ratings × 14 numbers); the time is the network: on
2026-10-08 the round trip to Singapore was **284 ms median, up to 630 ms** (143 ms on
2026-10-06), and single statements took 0.4–2.1 s. TZ FR-4 ("ta'm vektori 5 soniya
ichida", "optimistik UI") is not met in onboarding from this machine.

### Decisions (user, 2026-10-08)

1. **(a) fixed — the only code change of this check.** Two parts, each enough on its own:
   `finish()` drops every cached feed before it navigates (`useForgetRecommendations`
   in `queries.ts`), and Feed no longer acts on a cached "rate N more" while the feed is
   being fetched again: it shows the skeleton until the fresh answer arrives. Tests:
   `Onboarding.test.tsx` (finishing removes the cached feeds in both languages) and
   `Feed.test.tsx` (a cached "rate 10 more" during a refetch: skeleton, no redirect, then
   the feed); both fail without the fix.
2. **(b) not fixed — neither the optimistic "Next" nor fewer round trips on the server.**
   The 3:10 is driven by network latency, not by work: median 6.4 s per rating, 58 s
   for the 10, at a 284 ms round trip to Singapore. Deployed next to the database the
   round trip is ~1–2 ms, so the wait should go away by itself. Re-measure after deploy;
   if it is still slow then, come back to it.
3. **FR-3 verdict deferred.** Onboarding is timed again after deploy, on the live URL.
   3:10 minus the 58 s of saves is ~2:12, but that is an estimate, not a measurement.
4. **Lighthouse (item 5) deferred to after deploy**, on the live URL: a localhost build
   talking to a database in Singapore does not show production. The `lighthouse` package
   was not installed.
5. **Keyboard (3) and API off (6): the user, by hand.** The Chrome extension is not
   used for them.

### Feed speed: `GET /recommendations` (2026-10-06)

Account with the most ratings (32), 50 items in 4 sections, from this dev machine
to the main database (Supabase, Singapore). Read-only; no LLM.

| | Time |
|---|---|
| Network round trip to the database (`SELECT 1`, median of 5) | **143 ms** |
| HTTP, measured in the browser: first request after API start / then warm | **8.8 s** / **5.0 s, 4.3 s** |
| `recommend()` + explanation cache, service only (script), cold / warm | 6.8 s / **2.4 s** |

Warm request, from the API's SQL log (timestamps per statement):

| Part | Time | Statements |
|---|---|---|
| Before the first SQL (token check, connection checkout) | ~0.4 s | — |
| `ensure_user` (insert-if-missing + commit) | 0.27 s | 2 |
| Gap before the read transaction (new checkout) | ~0.5 s | — |
| Ratings count, user row | 0.40 s | 2 |
| Liked films with embeddings (32 × 1 536-d vectors) | **0.82 s** | 1 |
| Seen ids, `set_config` | 0.29 s | 2 |
| 4 sections × (candidates via HNSW + pairwise similarity for MMR) | **1.36 s** | 8 |
| Explanations cache | 0.13 s | 1 |
| **Total** | **~4.2 s** | 16 |

Where the time goes: every statement is one round trip to Singapore (~143 ms). 16
statements ≈ 2.3 s of pure latency, plus the embedding transfer (~0.7 s) and the checkout
gaps (~0.9 s). Work on the API's side is small: scoring, shortlist and MMR take **~0.03 s**
in total; the database's own work per query is ~10–50 ms above the round trip. Cold
start adds the band cuts' catalogue load (500 vectors, ~1.2 s once per 10 min) and the
reason rule (~0.3 s). TZ asks < 500 ms: with this many sequential round trips that is out
of reach while the API and the database are far apart — the number that matters is the
round trip from wherever the API is deployed. Not fixed (measurement only).

## Where the implementation differs from the design, and why

1. **Contrast.** `--faint` text is 3.5–4.2:1 on our backgrounds and white on `--red` is
   4.15:1, both under WCAG's 4.5:1. Meta text uses `--muted`; primary buttons and
   selected chips use `--red-dark` (6.25:1); numbers on trait bars stay `--text` while the
   bar carries the colour. The design's error colour `#FF6B7F` is not a token; errors use
   `--text` with a gold ⚠ (the prompt: "do not add colours").
2. **Assistant** is not in the navigation (Phase 4). **DNA** is always in the navigation;
   below 10 ratings it shows "rate N more" rather than hiding.
3. **Watchlist groups** are Watch next / Under 90 min / Watched. The trait-based groups
   (Challenging, Light, Hidden gems) are Phase 8 (`watchlist_groups.py`, TZ §2 item 12).
   Swipe actions are mobile (Phase 6); the web has buttons.
4. **DNA summary** is a sentence built from the three strongest traits, not an AI one
   (needs a cache table and a cost decision — backlog). **Share** uses the system share
   sheet or copies text; the server-side image (FR-7) is backlog.
5. **Search** has no streaming-provider filter: the catalogue has no provider data.
6. **Liked-aspect chips** list all 14 traits; the design shows ~5 film-specific ones
   (backlog: send the film's strongest traits with the onboarding list).
7. **Comparison bars**: the user's taste is a tick on the film's bar, not a second
   lighter bar (the two-layer version hid the film whenever the taste was higher).
8. **Onboarding grid** shows titles under posters: without poster images the tiles
   would be unrecognisable.

## Needs the user

- `apps/web/.env`: `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (public values, but
  kept out of git like every key). Without them `/welcome` says sign-in is not set up.
- Supabase dashboard: enable Google (a Google Cloud OAuth client) and add
  `http://localhost:5173/` and the production URL to the redirect allow-list.
- **Apple sign-in needs an Apple Developer Program membership ($99/year).** Not started:
  a paid plan is the user's decision. Until then the Apple button says the method is not
  switched on.
- ~~The API verifies HS256 tokens with `SUPABASE_JWT_SECRET`.~~ Resolved 2026-09-30: the
  project signs with ES256 signing keys, and the API now verifies against the project's
  JWKS (`SUPABASE_PROJECT_URL`, ADR 0007).
