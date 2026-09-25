# Phase 6 — Flutter application

Read `CLAUDE.md` first. **Phase 5's product gate must have passed**, not just its tests.
If the 15% metric was not met, you should not be reading this.

## Before you start

Read:
- `apps/mobile/README.md` and `apps/mobile/lib/theme/tokens.dart`
- The design system document — the platform parity table in particular
- `apps/web/src/lib/api.ts` — the Dart client mirrors it

## Goal

An iOS and Android app with feature parity to the web app, on test channels in both stores.

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
   - Apple Developer and Google Play accounts; signing set up.
   - Builds on TestFlight and Play internal testing.

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
- [ ] Both builds installed from TestFlight and Play internal testing by someone else.

## Report

1. Gate output.
2. Device list, cold start times, onboarding time.
3. Where mobile had to diverge from web, and whether the parity table needs updating.
4. Do not start Phase 7.
