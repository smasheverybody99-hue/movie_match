# Phase 9 — Launch readiness

Read `CLAUDE.md` and `docs/legal.md` first. Phase 8's gate must be green.

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
   - Sentry on API, web and mobile, with release tagging.
   - Uptime monitoring with alerting to a channel you actually read.
   - Database backups **and a restore you have actually performed**. Restore into a scratch
     database and report how long it took and whether the data was intact.
   - A documented rollback: how to get back to the previous version in under 10 minutes.
4. **Store submission**
   - App Store and Play submissions, with privacy nutrition labels filled in honestly.
   - Expect rejection on the first attempt. Budget 1–7 days per review round.
5. **Launch surface**
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
0–8 still passes.**

Manual checklist:
- [ ] TMDB attribution verified in the live app; commercial licence signed IF monetizing
- [ ] Restore from backup performed; time and integrity reported
- [ ] Rollback rehearsed once
- [ ] Load test at 2× expected launch traffic
- [ ] Both store submissions sent; review status reported
- [ ] Privacy policy and terms live and linked
- [ ] A real person who has never seen the app completes sign-up unaided while you watch,
      saying nothing. Report where they hesitated.

## Report

1. Gate output.
2. The restore test result.
3. Store review status.
4. What the unaided sign-up test revealed.
5. A go / no-go recommendation with the reason.
