# Phase 9b — Store launch (Google Play)

Read `CLAUDE.md` and `docs/legal.md` first. Split from Phase 9 by TZ 1.30; the web launch
is `phase-09a-web-launch.md`. Target: **submission on 2026-12-12; visible in the store
not before 2026-12-19** (Google's review usually takes up to seven days).

Preconditions:
- Phase 9a done: the web is public and its legal, security and reliability work applies
  here too (same API, same privacy policy and terms).
- Phase 6's gate green. **Phases 7 and 8 are not required** (TZ 1.31): they ship after
  the store launch as updates, Character Match behind its flag until the lawyer's review.
- Phase 5's product gate passed, both 15% and 70% (TZ 1.31). Otherwise nothing is
  submitted.
- **Google Play:** a personal developer account created after 2023-11-13 must run a
  closed test with at least 12 testers opted in continuously for at least 14 days, then
  apply for production access; Google says review "usually takes seven days or less, but
  can occasionally take longer"
  ([Play Console Help, answer 14151465](https://support.google.com/googleplay/android-developer/answer/14151465),
  checked 2026-11-13). A closed test that starts 2026-11-28 reaches 14 days on 2026-12-12
  at the earliest — no slack.
- **App Store: not in this phase** (TZ 1.31). iOS is a separate decision in January
  2027; it will need an Apple Developer Program membership (99 USD a year) and an iOS
  build made on macOS — from this Windows machine, a cloud build.

No new features this phase.

## Build

1. **Store submission**
   - Play: apply for production access after the closed test (the form asks about the
     closed test, the app and production readiness); then the production release.
   - The Data safety form (Play) filled in honestly, from the same data inventory as the
     privacy policy.
   - Expect rejection on the first attempt. Budget 1–7 days per review round.
2. **Mobile reliability**
   - Sentry on mobile, with release tagging.
   - Crash-free check on the closed-test build before production.
3. **Store assets**
   - Icon, screenshots and listing text. No character names or imagery (docs/legal.md).

## Required tests

- Re-run the full suite from every previous phase, mobile included. Nothing may have
  regressed.
- `test_attribution.py`, `test_account_deletion_complete.py` and `test_data_export.py`
  from Phase 9a still pass (the stores ask for deletion and data use).

## Gate — do not skip

```bash
cd services/api && ruff check . && ruff format --check . && pytest -q --cov=app --cov-report=term-missing
cd apps/web && npm run lint && npm run typecheck && npm run build && npm test
cd apps/mobile && flutter analyze && flutter test
pip-audit && npm audit --audit-level=high
```

Pass condition: **all pass; no high or critical vulnerabilities; every test from phases
0–9a still passes.**

Manual checklist:
- [ ] Play closed test: 12 testers opted in for 14 consecutive days (dates reported)
- [ ] Play production access applied for; status reported
- [ ] Data safety matches the privacy policy

## Report

1. Gate output.
2. Play review status, and the date the app became visible.
3. A go / no-go recommendation for the store launch with the reason.
