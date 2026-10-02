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
