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

**The switch is `ASSISTANT_ENABLED`** (added 2026-11-24, user decision): an API setting,
default `true`, that `GET /me` reports as `assistant_enabled`. The Android app shows its
Assistant tab only while it is `true`, so turning it off removes the tab from every phone
without a new APK. For this launch, in this order:

1. Render → the API service → Environment: `ASSISTANT_ENABLED=false`; the service redeploys.
2. `GET /me` (signed in) answers `"assistant_enabled": false`.
3. The Android app, opened again (or back from the background), has no Assistant tab;
   one left on the assistant goes back to Home.
4. Still to build here: the web reads the same field (no route, no navigation entry), and
   `POST /assistant/chat` refuses while it is false (the flag alone hides the entry points;
   it does not close the endpoint).

To bring the assistant back: the paid tier, FR-8 measured, then `ASSISTANT_ENABLED=true`.

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

### Google sign-in in production (added 2026-11-27; corrected 2026-11-27)

The OAuth consent screen moves from **Testing** to **In production** before the web launch.
Today (checked by the user 2026-11-27): Google Cloud project "Default Gemini Project"
(`gen-lang-client-0014845015`), Google Auth Platform → Audience, Publishing status = Testing,
4 test users of a 100 limit. The alpha stays in Testing; the user adds each tester's Gmail to
Test users (`docs/STATUS.md`, "Alfa tayyorgarligi").

**Decision (user, 2026-11-27): no brand verification for the web launch — there is no
money for it.** Before 2026-12-15 the only step is "Publish app" → In production. The consent
screen then shows `<ref>.supabase.co`, not "Movie Match" and the logo, as in the alpha today;
this is accepted. Brand verification (our own domain + a Supabase custom domain) is
**backlog**: when money is found, check the prices at that time and ask the user before
buying or starting anything. The notes below stay for that day.

What the pages say (read 2026-11-27; sources below):

- **Scopes.** Both apps call Supabase `signInWithOAuth` with no `scopes`
  (`apps/web/src/lib/supabase.ts`, `apps/mobile/lib/auth/auth_client.dart`); Supabase Auth's
  Google default is `email` and `profile` (supabase/auth `internal/api/provider/google.go`).
  Non-sensitive: no scope verification, no user cap.
- **Not required.** "If your app utilizes only non-sensitive scopes, it is not mandatory for your
  app to complete the app verification process." Without it, "only your application domain will
  be visible to users."
- **How long, if chosen.** The automated check "typically takes a few minutes"; a manual review
  "usually takes 2-3 business days" (Supabase: "may take a few business days"). A compliant
  result is valid for **7 days**: not published within them, it goes back to "Need to re-verify".
- **What is checked.** App name (no Google product names); logo (JPG/PNG/BMP, ≤ 1 MB, ideally
  120×120); a home page on a verified domain, describing the app and **not only a login page**
  (the landing page in Build 4 first), linking the privacy policy; the privacy policy on the
  home page's domain, the same URL as on the consent screen, saying how Google user data is
  accessed, used, stored and shared; a terms link; **every authorized domain verified in Google
  Search Console** by a project owner or editor; current contact details.

**The domain (checked 2026-11-27; nothing bought or created).**

- `movie-match.pages.dev` can be the home page and an authorized domain in principle: `pages.dev`
  is on the Public Suffix List (private section, Cloudflare; list version 2026-11-27), so
  `movie-match.pages.dev` is its own "top private domain", which is what Google asks to verify.
  Search Console verifies a URL-prefix property (`https://movie-match.pages.dev/`) with an HTML
  file or meta tag, no DNS needed; a Domain property needs DNS, so not on pages.dev.
  **Not confirmed:** no page says a URL-prefix verification satisfies the OAuth
  authorized-domain check. The free way to find out: verify it in Search Console and see whether
  Branding accepts it.
- **The likely obstacle is the Supabase callback.** Google: authorized domains "also need to
  include the redirect URIs" of a Web application client, and every authorized domain must be
  verified. Our redirect URI is on `<ref>.supabase.co`; `supabase.co` is on the Public Suffix List
  too, so `<ref>.supabase.co` would need verifying, and we cannot put a file at its root.
  Supabase's own guide: without a custom domain "users will see `<project-id>.supabase.co`", and
  it calls a custom domain "strongly recommended". So brand verification likely needs our own
  domain **and** a Supabase custom domain, both paid (prices not checked). Ask before any of it.
- Without brand verification the consent screen shows `<ref>.supabase.co`, as in the alpha today.

If brand verification is done later, it depends on the lawyer too: it cannot be submitted
before the privacy policy and terms (drafts waiting for the lawyer's review, `docs/legal-drafts/`,
`docs/STATUS.md` "yurist uchun ochiq masalalar") are published on the home page's domain.

**Backlog — not for this launch (user, 2026-11-27).** The dates worked out on 2026-11-27 for
the case where brand verification was chosen before a 2026-12-15 launch, kept only as a
template for when money is found (re-date them then):

| By (backlog) | Step | Who |
|---|---|---|
| ~~2026-12-04~~ backlog | Domain settled (own domain + Supabase custom domain: paid, check prices then, ask first); Search Console verified; consent screen fields filled | user |
| ~~2026-12-07~~ backlog | Privacy policy and terms published after the lawyer's review | user + lawyer |
| ~~2026-12-08~~ backlog | "Verify branding" pressed (2-3 business days, room for one fix) | user |
| within 7 days of a compliant result | Brand shows on the consent screen (the app is already In production) | user |

**For this launch only one step: "Publish app" → In production, before 2026-12-15** (user).

Sources: https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification,
https://support.google.com/cloud/answer/13464321, https://support.google.com/cloud/answer/13463073,
https://support.google.com/cloud/answer/15549049, https://support.google.com/cloud/answer/15549945,
https://support.google.com/webmasters/answer/9008080,
https://supabase.com/docs/guides/auth/social-login/auth-google,
https://github.com/supabase/auth/blob/master/internal/api/provider/google.go,
https://publicsuffix.org/list/public_suffix_list.dat.

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
- [ ] Google OAuth In production ("Publish app", before 2026-12-15); record what the consent
      screen shows (`<ref>.supabase.co` expected and accepted). Brand verification — backlog
      (user, 2026-11-27: no money; own domain + Supabase custom domain, ask first)
- [ ] A real person who has never seen the app completes sign-up unaided while you watch,
      saying nothing. Report where they hesitated.

## Report

1. Gate output.
2. The restore test result.
3. What the unaided sign-up test revealed.
4. A go / no-go recommendation for the public web launch with the reason.
5. Do not start Phase 9b without the user.
