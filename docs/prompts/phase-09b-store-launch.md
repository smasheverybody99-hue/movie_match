# Phase 9b — Store launch

Read `CLAUDE.md` and `docs/legal.md` first. Split from Phase 9 by TZ 1.30; the web launch
is `phase-09a-web-launch.md`. Target: **submissions on 2026-12-12.**

Preconditions:
- Phase 9a done: the web is public and its legal, security and reliability work applies
  here too (same API, same privacy policy and terms).
- Phases 6, 8 and 7 gates green. Character Match may ship **behind its flag, off**, until
  the lawyer's review is recorded in `docs/legal.md` (Phase 7).
- Phase 5's product gate passed. If the 15% metric failed, nothing is submitted.
- **Google Play:** a personal developer account created after 2023-11-13 must run a
  closed test with at least 12 testers opted in continuously for at least 14 days, then
  apply for production access; Google says review "usually takes seven days or less, but
  can occasionally take longer"
  ([Play Console Help, answer 14151465](https://support.google.com/googleplay/android-developer/answer/14151465),
  checked 2026-11-13). A closed test that starts 2026-11-28 reaches 14 days on 2026-12-12
  at the earliest — no slack.
- **App Store:** Apple Developer Program membership (99 USD a year), an iOS build made on
  macOS (Xcode is required; from this Windows machine that means a cloud build) and
  TestFlight. Whether iOS goes on 2026-12-12 is the user's decision; this file does not
  assume it.

No new features this phase.

## Build

1. **Store submission**
   - Play: apply for production access after the closed test (the form asks about the
     closed test, the app and production readiness); then the production release.
   - App Store (when the user decides): App Store Connect record, TestFlight, review.
   - Privacy labels (App Store) and the Data safety form (Play) filled in honestly, from
     the same data inventory as the privacy policy.
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
- [ ] App Store submission sent, if the user decided iOS goes now; status reported
- [ ] Data safety and privacy labels match the privacy policy
- [ ] Character Match flag state recorded (off unless the lawyer's review is in)

## Report

1. Gate output.
2. Store review status, per store.
3. A go / no-go recommendation for the store launch with the reason.
