# Phase 9a — Web launch readiness and the public web launch

Read `CLAUDE.md` and `docs/legal.md` first. TZ 1.30 split Phase 9 in two: this file is the
web launch (target **2026-12-15**); the store submission is `phase-09b-store-launch.md`
(paused until the $25 Play account, TZ 1.37; TZ 1.31: it does not wait for Phases 7 and 8).

Preconditions (TZ 1.30): the readiness work below is built **during the alpha**, from
2026-11-29. The public launch itself needs **Phase 5's product gate passed** (decision
2026-12-13): both 15% and 70% (TZ 1.31). If 15% fails, the engine is reworked; if 70%
fails, onboarding is fixed and measured again. Either way this launch waits. Phases 7
and 8 come after the store launch and are not required for it.

**An AI-free launch (TZ 1.38, user decision 2026-11-23).** There is no money for the
Gemini paid tier (a $50 card hold), so the web launches with no Gemini call from any
request: the assistant is hidden (behind a flag: no route, no navigation entry, and the
endpoint refuses), and the film page's "why you'll like this" comes from the
`explanations` cache or, failing that, a template sentence from `named_traits`. Build
it in this phase, not before. When money is found, the paid tier goes on, FR-8 is
measured (below), and only then does the assistant come back.

Three more preconditions, all required:

- **No Gemini call from a request** (TZ 1.38): assistant hidden, explanations from the
  cache or a template only, with a test that fails if a request reaches the provider.
  (Before TZ 1.38 this was "Gemini paid tier"; ADR 0004's free-tier exception stays
  alpha-only.)
- **FR-8 first character, measured again** (TZ 1.33) — **when the assistant comes back on
  the paid tier, not for this launch** (TZ 1.38). Phase 4 closed without meeting it
  (33 messages, median 3.62 s, 1 error, free tier). After the switch to the paid tier,
  measure on the client with the page connected: at least 30 messages on at least two
  different days, median ≤ 3 s, 90th percentile ≤ 15 s, no message ending in `error`.
  Ask before the run: it is paid. If it fails, the launch does not happen. The criterion
  is not softened again.
- **The film page's speed, measured again** (TZ 1.34). Phase 4 closed with F3 item 5 open:
  on the live site the film page's mobile LCP was 4.6 s (median of 14.5, 4.2 and 4.6 s;
  desktop 1.4 s), and INP was not measured. On the live site, Lighthouse mobile, the median of
  three runs: **LCP < 2.5 s**, and **INP < 200 ms** in a timespan that presses Rate and Save.
  If either fails, the launch does not happen. Cause and fixes: `docs/phase-3-status.md`, item 5.

No new features this phase. Everything here is about being safe to put in front of
strangers.

## Build

1. **Legal**
   - TMDB: attribution in place (required on the free tier too). The commercial licence
     is required only if this launch ships a revenue mechanism — subscriptions, ads, paid
     tiers. If it does and the licence is not signed, launch does not happen; say so
     plainly rather than launching anyway. See ADR 0002 and docs/legal.md.
   - TMDB attribution: logo unmodified plus the exact required sentence, in About.
   - Terms of Service and Privacy Policy published and linked from sign-up.
   - Data export and account deletion working end to end, not just present.
2. **Security**
   - No secret in any tracked file. Verify with a secret scanner over the whole history,
     not just the working tree.
   - Every endpoint authorised; re-run the cross-user isolation tests.
   - Rate limits on auth, assistant and write endpoints.
   - Dependency audit: `pip-audit` and `npm audit`. Report and fix anything high or above.
     Known carry-over from phase 0 (2026-09-25): GHSA-82fw-gwwq-j7x9, a moderate path
     traversal in `@vitest/mocker` (via vitest 3.2.x and `@vitest/coverage-v8`). Dev toolchain
     only; `npm audit --omit=dev` is clean, so it does not reach the bundle. Fixed from vitest
     4.1.11. `--audit-level=high` will not flag it, so resolve it here explicitly.
3. **Reliability**
   - Sentry on API and web, with release tagging (mobile in Phase 9b).
   - Uptime monitoring with alerting to a channel you actually read.
   - Database backups **and a restore you have actually performed**. Restore into a scratch
     database and report how long it took and whether the data was intact.
   - A documented rollback: how to get back to the previous version in under 10 minutes.
4. **Launch surface**
   - Landing page, analytics, onboarding funnel instrumented.
   - Status page or a way to tell users when something is broken.

## Required tests

- `test_secrets_scan.py` — CI fails if a pattern matching an API key appears in tracked
  files
- `test_attribution.py` — the About payload contains the exact TMDB sentence and logo
  reference; the test fails if the string is altered
- `test_data_export.py` — export contains every table holding that user's data; a new user
  with no data gets a valid empty export
- `test_account_deletion_complete.py` — after deletion, a query across every user-scoped
  table returns zero rows for that id
- `test_rate_limits.py` — auth, assistant and write endpoints each return 429 past their
  limit, with a reset hint
- Re-run the full suite from every previous phase. Nothing may have regressed.

## Gate — do not skip

```bash
cd services/api && ruff check . && ruff format --check . && pytest -q --cov=app --cov-report=term-missing
cd apps/web && npm run lint && npm run typecheck && npm run build && npm test
cd apps/mobile && flutter analyze && flutter test
pip-audit && npm audit --audit-level=high
```

Pass condition: **all pass; no high or critical vulnerabilities; every test from phases
0–6 still passes** (Phase 6's mobile code exists by now; Phases 7 and 8 come later).

Manual checklist:
- [ ] TMDB attribution verified in the live app; commercial licence signed IF monetizing
- [ ] Restore from backup performed; time and integrity reported
- [ ] Rollback rehearsed once
- [ ] Load test at 2× expected launch traffic
- [ ] Phase 5's product gate passed (record the 15% and 70% numbers with their intervals)
- [ ] No Gemini call from any request (TZ 1.38): assistant hidden, explanations from the
      cache or the template. (Later, when the assistant returns: paid tier on and FR-8
      passed on it, TZ 1.33: message count, days, median, 90th percentile, errors)
- [ ] Film page on the live site (TZ 1.34): mobile LCP median of three runs < 2.5 s, INP
      < 200 ms; record each run, the LCP element and the build's commit
- [ ] Privacy policy and terms live and linked
- [ ] A real person who has never seen the app completes sign-up unaided while you watch,
      saying nothing. Report where they hesitated.

## Report

1. Gate output.
2. The restore test result.
3. What the unaided sign-up test revealed.
4. A go / no-go recommendation for the public web launch with the reason.
5. Do not start Phase 9b without the user.
