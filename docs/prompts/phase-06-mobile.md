# Phase 6 — Flutter application

Read `CLAUDE.md` first. **Phase 5's technical gate must be green and the alpha testers
in** (target 2026-11-19). This phase runs while the alpha does and does not wait for its
product gate (TZ 1.30). If the 15% metric fails on 2026-12-03, work here may continue but
nothing goes to a public store track.

**Android first** (TZ 1.30): the Google Play closed test starts 2026-11-28 with the 12
alpha testers. A new personal Play developer account needs a closed test of at least 12
testers opted in for 14 consecutive days before it can apply for production
([Play Console Help, answer 14151465](https://support.google.com/googleplay/android-developer/answer/14151465),
checked 2026-11-13). **iOS is not planned now** (TZ 1.31): Android first; iOS is a
separate decision in January 2027. It will need a macOS build (cloud) and an Apple
Developer membership.

## Before you start

Read:
- `apps/mobile/README.md` and `apps/mobile/lib/theme/tokens.dart`
- The design system document — the platform parity table in particular
- `apps/web/src/lib/api.ts` — the Dart client mirrors it

## Goal

An Android app with feature parity to the web app on the Google Play closed test track by
2026-11-28. iOS is out of this phase until the January decision.

## Build

1. **Project setup**
   - `flutter create` if not done, then Riverpod, Dio, go_router, Isar.
   - Bundle Playfair Display and Inter as app fonts so typography matches the web exactly.
   - `--dart-define=API_URL=...`; never hard-code the URL.
2. **API client** — `lib/data/api_client.dart`
   - Mirrors the web client: bearer token, typed models, an `ApiException` with a status.
   - Models generated or hand-written to match `app/schemas.py`. Keep them in one file so
     drift is visible.
3. **Screens** — same order as the web app: auth, onboarding, feed, film, search,
   watchlist, DNA, assistant. Same four states each.
4. **Native behaviour** (the parity table is the contract)
   - Swipe to rate; swipe on watchlist rows.
   - Native share sheet for DNA and film pages.
   - Offline reading via Isar: cached feed and film pages work with no network.
   - Push via FCM: weekly recommendation, watchlist film became available.
5. **Release plumbing**
   - App icons, splash, store metadata.
   - Google Play developer account (identity and Android device verification) and signing.
   - Android build on the Play closed test track with the 12 alpha testers (2026-11-28).
   - The app records the same Phase 5 events as the web client, so alpha data from the
     phone is not lost.

## Out of scope

Character Match (Phase 7). Any feature the web app does not have.

## Required tests

Widget tests (`flutter test`) — for each screen: loading, empty, error, content states.

Specifically:
- `onboarding_test.dart` — continue disabled below 10; enabled at 10; state restored after
  an app restart
- `feed_test.dart` — sections render; empty section is omitted; match badge value correct
- `movie_page_test.dart` — optimistic rating rolls back on failure
- `watchlist_test.dart` — swipe actions fire the right calls
- `api_client_test.dart` — token attached; error mapped to `ApiException` with the status;
  timeout produces a retryable error
- `offline_test.dart` — with the network mocked as unavailable, cached content renders and
  the offline banner shows
- `tokens_test.dart` — the colour values equal those in `apps/web/src/styles/tokens.css`
  (parse the CSS file in the test; do not copy the values by hand)

## Gate — do not skip

```bash
cd apps/mobile && flutter analyze && flutter test
cd services/api && ruff check . && pytest -q
cd apps/web && npm run lint && npm run typecheck && npm test
```

Pass condition: **all pass; `flutter analyze` reports zero issues, not just zero errors.**

Manual checklist:
- [ ] Run on at least 4 real devices including one old Android. Report models.
- [ ] Cold start time, release build, on the slowest device. Target under 2s.
- [ ] Complete onboarding on a phone, timed.
- [ ] Airplane mode: open the app, browse cached content, come back online. No crash,
      no stuck spinner.
- [ ] The Android build installed from the Play closed test by someone else; the 12
      testers opted in (the 14 days start from the last one in).

## Report

1. Gate output.
2. Device list, cold start times, onboarding time.
3. Where mobile had to diverge from web, and whether the parity table needs updating.
4. Do not start the next phase in TZ 1.30's order (Phase 9a) without the user.
