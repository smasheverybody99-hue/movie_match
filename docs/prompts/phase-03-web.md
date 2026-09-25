# Phase 3 — Web application

Read `CLAUDE.md` first. Phase 2's gate must be green, including your verdict on the
30-rating test.

## Before you start

Read:
- The design system document (`docs/roadmap.html` links it; the artifact is the source
  of truth for screens, tokens and states)
- `apps/web/src/styles/tokens.css` — the tokens already exist; use them, do not add colours
- `docs/TZ.md` sections 4 (FR-3, FR-4, FR-5, FR-7) and 5
- `apps/web/src/lib/types.ts` — keep it in sync with the API schemas

## Goal

A web application a stranger can sign up for and use, covering onboarding, the feed, film
pages, rating, watchlist and Movie DNA.

## Decide first

SEO: film pages benefit from server rendering. Decide now whether to migrate to Next.js
or stay on Vite, and write the decision into `docs/decisions/0002-web-framework.md`
before writing screens. Migrating later costs a week; decide it in the first hour.

## Build

Screens, in this order — each one complete (all four states) before the next:

1. **Auth** — Google, Apple, email magic link. Supabase client in `src/lib/supabase.ts`;
   push the access token into `api.setAccessToken` on every session change.
2. **Onboarding** — pick films (min 10), rate them, liked-aspect chips above 8.0.
   Progress survives a reload: a user who leaves mid-way resumes where they were.
3. **Home feed** — sections with reasons, horizontal card rows, match badges.
4. **Film page** — backdrop, match ring, "why you'll like this", trait comparison,
   rate and watchlist buttons.
5. **Search** — query, filters (year, runtime, traits, providers).
6. **Watchlist** — smart group chips, rows, mark watched, remove.
7. **Movie DNA** — trait bars sorted by strength, AI summary, stats, share.

Cross-cutting:
- i18n from the start (`uz` and `en`). No hard-coded user-facing string anywhere.
- Every screen implements loading (skeleton), empty, error and offline states.
- Optimistic updates for rating and watchlist, rolled back on failure.

## Out of scope

Assistant (Phase 4). Character Match (Phase 7). Group features (Phase 8).

## Required tests

Component tests (`vitest` + React Testing Library) — for each screen:
- renders its loading state
- renders its empty state with the right call to action
- renders its error state with a retry that refetches
- renders real content from a mocked API response

Specifically:
- `Onboarding.test.tsx` — continue is disabled below 10 picks; enabled at 10; liked-aspect
  chips appear above 8.0 and not below; progress restores after a remount
- `Feed.test.tsx` — sections render; a section with no items is not rendered at all;
  match badge shows the API's number
- `MoviePage.test.tsx` — rating optimistically updates and rolls back on a failed request;
  the explanation skeleton shows while it loads
- `Watchlist.test.tsx` — group chips filter the list; mark-watched removes the row
- `Dna.test.tsx` — below 10 ratings shows the "rate more" screen, not empty bars
- `api.test.ts` — attaches the bearer token; throws `ApiError` with the status on failure
- `i18n.test.ts` — every key present in `uz` exists in `en` and vice versa

## Gate — do not skip

```bash
cd apps/web && npm run lint && npm run typecheck && npm run build && npm test
cd services/api && ruff check . && pytest -q
```

Pass condition: **all pass; no TypeScript errors; no `any` in the codebase
(`grep -rn ": any" src/` returns nothing).**

Manual checklist:
- [ ] Complete onboarding as a brand-new user, timed. Report the time. Target: under 3 min.
- [ ] Every screen at 320px width: nothing clipped, no horizontal scroll.
- [ ] Keyboard only: reach and activate every control on every screen.
- [ ] Run axe (browser extension or `@axe-core/cli`) on each screen; report violations.
      Contrast and label violations must be zero.
- [ ] Lighthouse on the film page: report LCP and INP. Targets: LCP < 2.5s, INP < 200ms.
- [ ] Turn the API off and walk through every screen. No white screens, no raw error text.

## Report

1. Gate output.
2. The framework decision and why.
3. Onboarding completion time, axe results, Lighthouse numbers.
4. Screens where the design and the implementation differ, and why.
5. Do not start Phase 4.
