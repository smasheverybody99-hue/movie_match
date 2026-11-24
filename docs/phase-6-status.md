# Phase 6 — status

Last updated: 2026-11-24 · Phase: **6 (Android app), screens done, on `f6-mobile`** · the
user's phone test passed 2026-11-24 · merge into `main` approved by the user 2026-11-24

Phase prompt: `docs/prompts/phase-06-mobile.md`. Android first (TZ 1.30); the alpha testers
get the app as an APK from CI, without Google Play (TZ 1.37). Offline reading and push come
after 2026-12-08, as updates (user decision, 2026-11-23). No paid request was made for this
phase.

## Decisions (user)

| Question | Decision | When |
|---|---|---|
| Plan | ~14 commits, screens in the web's order, then release and CI; offline and push after 2026-12-08 | 2026-11-23 |
| Local database | `isar_community` instead of `isar` (no `isar` release since 2023-04) | 2026-11-23 |
| Builds | APK from CI (`.github/workflows/android.yml`): the local build did not finish in 15 min (5.8 GB RAM) | 2026-11-23 |
| Release signing | One fixed upload key outside the repo, its SHA-256 checked by CI (`UPLOAD_CERT_SHA256`) | 2026-11-23 |
| Assistant tab | As on the web, the third tab, **shown only while the server offers it**: `/me` `assistant_enabled` (setting `ASSISTANT_ENABLED`, default true; merged to `main` `f24db17`). F9a turns it off without a new APK | 2026-11-24 |
| Swipe to rate | Not in F6: the web has none. TZ backlog, F8 polish. Watchlist swipe is done | 2026-11-24 |
| Share | Android's own share sheet through a small channel in `MainActivity.kt` (no package installed); else copy, as the web does | 2026-11-24 |

## Built (branch `f6-mobile`)

| Commit | What | Tests | CI |
|---|---|---|---|
| `a339d45` … `1977512` | Scaffold, setup (fonts, tokens, `API_URL`), CI, API client and models | 39 | android 3, gate 143; merged `ae6f7ae` |
| `6d04b66` | Release APK signed with the fixed upload key; CI checks the signature | — | android 4, gate 146 |
| `568fb47` | Sign-in (Google, Apple, email link), data notice, strings generated from the web | 59 | android 6, gate 148 |
| `39678a8` | Onboarding (pick, rate, done), rating queue, onboarding telemetry | 90 | android 7, gate 150 (debug: settings missing then) |
| `d37e822` | Feed: hero, rows, band, Save, "Not right?", shown / clicked events | 132 | android 8 (**first release APK**), gate 153 |
| `a14241f` | Film page: why you, trait axes, optimistic rating, Save, sensitive warning | 161 | android 9, gate 155 |
| `0f48081` | Search with filters; the bottom bar | 174 | android 10, gate 157 |
| `6c9ba39` | Watchlist: groups, Watched / Remove, row swipe | 192 | android 11, gate 159 |
| `997f2b4` | Movie DNA: radial chart, stats, Numbers, Share | 211 | android 12, gate 160 |
| `da618ce` | Profile and About: language, sign out, delete account, TMDB attribution | 222 | android 13, gate 161 |
| `e2880f9`, `7302370` | Launcher icon from the mark, dark launch screen (and the XML comment fix) | 222 | android 14 failed, 15 green, gate 163 |
| `42afdb9` | Assistant: SSE stream, cards, limit, busy / failed with Try again; tab by the server | 243 | android 16, gate 164 |

Every screen has its four states (loading, empty, error, content) and a test that nothing
is cut off on a small phone (360 × 640) at text sizes 1.0, 1.3 and 2.0.

API (on `main`, user approval): `f24db17` — `GET /me` `assistant_enabled`
(`ASSISTANT_ENABLED`, default true), no migration; gate 168, `/health` → `f24db17`.

## Gate

Required tests (`phase-06-mobile.md`):

| Test | State |
|---|---|
| `onboarding_test.dart` — continue below / at 10, restored after a restart | Done |
| `feed_test.dart` — sections, empty section omitted, band | Done |
| `movie_page_test.dart` — optimistic rating rolls back | Done |
| `watchlist_test.dart` — swipe actions fire the right calls | Done |
| `api_client_test.dart` — token, `ApiException` with status, timeout retryable | Done |
| `tokens_test.dart` — colours parsed from `tokens.css` | Done |
| `offline_test.dart` — cached content and the offline banner | **Open**: offline reading is after 2026-12-08 |

Commands: `flutter analyze` 0 issues and `flutter test` 243 / 243, locally and in a clean
worktree; CI android run 16 green (release, signature matches), gate 164 green (API ruff +
pytest, web lint + typecheck + test).

## The user's phone test (2026-11-24)

Samsung Galaxy S9 (SM-G960F), Android 10 (API 29), One UI 2.5, security patch
2022-03-01; release APK from android run 16.

| # | Check | Result |
|---|---|---|
| 1 | Data notice | ✅ |
| 2 | Onboarding | ✅ — no waiting noticed (not timed) |
| 3 | Feed: hero, rows, Save | ✅ |
| 4 | Film page: rating, trait axes | ✅ |
| 5 | Search | ✅ |
| 6 | Assistant tab and an answer | ✅ |
| 7 | Movie DNA and Share | ✅ |
| 8 | Watchlist swipe | ✅ |
| 9 | Language switch | ✅ |
| 10 | Airplane mode | No crash; **after the network came back, ~7 s without a response** (below, "Known limits") |
| 11 | Cold start, release build | Normal, no noticeable wait (not timed) |
| — | Google sign-in | ✅ once the redirect URL was added to the main Supabase project (`docs/setup-android.md`, "Muammo bo'lsa: kirish") |

## Manual checklist (`phase-06-mobile.md`)

- [x] One old Android among them — the Galaxy S9 on Android 10 (API 29), 2018 hardware
      (user, 2026-11-24).
- [ ] At least 4 real devices — **one so far** (Galaxy S9).
- [ ] Cold start under 2 s on the slowest device — "normal" on the S9, not timed.
- [x] Complete onboarding on a phone — done, not timed.
- [ ] Airplane mode: browse cached content, come back online — no crash; cached browsing
      waits for offline reading (after 2026-12-08); the ~7 s after reconnecting is open.
- [ ] A tester installs the APK from `docs/testers-android.md` without help.

## Where mobile diverges from the web

Each is written in the screen's own header comment. The main ones: slides and rows are
swiped; pull to refresh; no hover-only quick Rate / Save on cards; "Not right?" and the
rating open in bottom sheets; the filters fold; the watchlist chips wrap and its rows swipe;
the film page covers the bottom bar; profile opens from a person icon in each top bar; Share
and the TMDB link go through Android. The parity table itself is in the v1 design artifact;
`docs/ui.md` section 10 has the status of the phone-only behaviours.

## Known limits

- **~7 s after the network returns** (phone test, item 10). Likely cause, not confirmed
  with the phone's network log: the first request after the radio returns loses its
  connection packets while the data path settles, and the system's connect retries (1 s,
  then 2, then 4: ~7 s) ran inside the 15 s connect timeout. Fix on `mobile-reconnect`
  (`32fd246`): connect timeout 5 s, and a GET whose connection failed or timed out is sent
  once more; POST / DELETE never. Android run 18 green; the merge waits for the user.
  Check on the phone: airplane mode on, then off, then pull to refresh on Home.

Merged into `main` 2026-11-24: `d708751` (gate 172, android run 17 release, `/health` →
`d708751`). The APK for the alpha testers: android run 17, artifact
`movie-match-d7087513f9b5c2d09cc599a28ad7d7b4e13b9e82` (until 2026-12-08).
- Offline reading (Isar) and push (FCM): after 2026-12-08.
- Store metadata and the Play closed test: Phase 9b.
