# Phase 9b — Store launch (Google Play)

Read `CLAUDE.md` and `docs/legal.md` first. Split from Phase 9 by TZ 1.30; the web launch
is `phase-09a-web-launch.md`. Target (TZ 1.37, 2026-11-23): **paused until the $25 Play developer account is paid for**
— or until option B, a trusted person's existing account at $0, is chosen (TZ 1.39, below).
The closed test starts once the account exists and 12 testers are in; submission 14 days
after the 12th opts in; visible after Google's review (usually up to seven days). Until
then the alpha testers use an APK file (Phase 6).

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
  checked 2026-11-13). The 14 days count from the day the 12th tester opts in.
- **App Store: not in this phase** (TZ 1.31). iOS is a separate decision in January
  2027; it will need an Apple Developer Program membership (99 USD a year) and an iOS
  build made on macOS — from this Windows machine, a cloud build.

No new features this phase.

## Account options (TZ 1.39, 2026-11-24) — decision pending

TZ §2 "Play akkaunti variantlari" compares A (my own account, $25, a new personal account,
so the 12 × 14 closed test is mandatory) and B (an account a trusted person — a parent or
relative — already has; they invite me as Admin, I pay nothing). The user decides; nothing
here starts before that. Facts and sources are in the TZ section (Play Console Help, read
2026-11-24).

Steps for **B**:

1. **Ask the owner** whether the account exists, when it was created and whether it is
   personal or an organization account. Created before 2023-11-13, or an organization:
   no closed test requirement. Created after, and personal: the 12 × 14 rule applies as
   in A (step 6).
2. **The owner invites me** (Users and permissions → invite → "Make this user an account
   admin"). The owner stays the developer named on the store page, and the person named
   in the privacy policy unless the lawyer says otherwise (`docs/legal-drafts/README.md`,
   item 9).
3. **`applicationId` is `com.moviematch.movie_match`** (`apps/mobile/android/app/build.gradle.kts`)
   and **never changes after the first upload**: Play identifies the app by it, and a new
   id is a new app with no reviews, testers or history. Check it once more before the first
   upload; do not rename it afterwards (the sign-in redirect scheme
   `com.moviematch.moviematch` is separate and may change).
4. **Play App Signing on** (the default for a new app). Google keeps the app signing key;
   the **upload key stays with me**: the existing `.jks` outside the repo
   (`C:\Users\User\.moviematch-keys`, certificate SHA-256 in `.github/workflows/android.yml`,
   `UPLOAD_CERT_SHA256`). If it is lost, an Admin asks Google for an upload key reset — the
   app is not lost. The key never goes to the account owner.
5. **Upload format.** Play takes an Android App Bundle for new apps; CI builds only APKs
   today. Add a `flutter build appbundle --release` step signed with the same upload key
   (not re-checked on the Play page 2026-11-24; confirm before the first upload).
6. **If the B account is new (personal, after 2023-11-13): run the alpha through the Play
   closed test track.** One 14-day window then covers both the Phase 5 gate (two weeks of
   alpha) and Play's requirement, instead of two in a row. Conditions: 12 testers opted in
   continuously for 14 days, counted from the 12th opt-in (one who leaves and rejoins does
   not count); every tester joins with the Gmail on their Android phone. Note: a Play
   build is re-signed with Google's app signing key, so it cannot update an APK installed
   from CI (different signature): testers uninstall the CI APK once, then install from
   Play. Ratings live on the server and are not lost.
7. **Later, app transfer** to my own account is possible (both accounts registered, active,
   within policy; my account then costs $25). Test groups do not transfer. Open question,
   not answered by the page: whether a new personal target account must then run its own
   12 × 14 test — ask Play support before transferring.

Moved here from Phase 6 by TZ 1.37: the Play developer account (identity and Android
device verification), release signing for Play, and the closed test track.

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
