# Legal drafts: for the lawyer's review, not published

Written 2026-11-23 by Claude, on the user's request; updated 2026-11-27 (AI-free launch,
log retention, deletion and export branches). **Not legal advice and not
final.** Nothing here is live in the app.

| File | What |
|---|---|
| `privacy-policy.en.md`, `privacy-policy.uz.md` | Privacy policy, English and Uzbek |
| `terms.en.md`, `terms.uz.md` | Terms of use, English and Uzbek |
| `tmdb-licence-request.en.md` | Email draft to TMDB sales (not sent) |

Blanks are `[____]`: names, contact details, address, company form, ages, dates. They are
left for the user and the lawyer. The English text is the source; the Uzbek follows it
section by section.

## What the drafts describe: facts checked in the code, 2026-11-23

- **Data stored:** account email from Supabase Auth; ratings (with liked aspects); the
  watchlist and "watched" marks; dismissed films; "Not right?" feedback; assistant
  questions and answers; daily usage counters; usage events (what was shown, opened or
  tapped, film id, screen, time); when the data notice was accepted; a taste profile
  computed from ratings.
- **Where:**
  - Database and Auth: Supabase, Singapore region.
  - API: Render, Singapore.
  - Website: Cloudflare Pages.
  - AI: Google Gemini API — **during the closed alpha only.** The web launch is AI-free
    (TZ 1.38): no request calls Gemini; explanations come from the stored cache or a
    template sentence; the assistant is hidden.
  - Images: loaded from TMDB's servers.
- **Deleting an account** (`DELETE /me`) removes every app row belonging to the user
  (ON DELETE CASCADE).

## Gaps the lawyer and the user must see (not fixed)

1. **The sign-in record survives account deletion.** `services/users.py` says the Supabase
   Auth identity, which holds the email, is not touched. The policy promises full
   deletion, so before launch either the code removes the Auth user too, or the policy
   says otherwise. **Fix built 2026-11-27 on branch `account-delete-auth`, not merged:**
   `DELETE /me` deletes the `auth.users` row in the same transaction (no new key: the
   API's database role may delete there). Closed once merged and live.
2. **There is no data export.** `docs/legal.md` §3 says export "must actually work". The
   drafts promise it on request by email, done by hand, until a feature exists. **Built
   2026-11-27 on branch `data-export`, not merged:** `GET /me/export` and Profile →
   "Download my data" on the web (one JSON file: every table holding the user's rows,
   the sign-in record, film titles). The Android app has no button yet. Closed for the
   web once merged and live.
3. **Data localisation (Uzbekistan).** The Law on Personal Data (No. ZRU-547), as
   amended in 2021, is understood to require that personal data of citizens of
   Uzbekistan be processed and stored on servers located in Uzbekistan. Our database is in
   Singapore. **The lawyer must check this first:** it can change where the database
   must live, not just the text.
4. **Minimum age.** Left blank for the lawyer: 13, 16 or 18 depending on the law the
   lawyer applies.
5. **The alpha's free-tier exception** (ADR 0004). During the closed alpha, Google may use
   what the assistant is sent. **Updated 2026-11-27:** the launch text now says the
   service calls no AI provider (TZ 1.38), with stored alpha-era explanations named; the
   alpha paragraph stays marked "ALPHA ONLY"; a marked "LATER" paragraph says the section
   is rewritten before the assistant returns on the paid tier. Lawyer: whether alpha-era
   text shown after launch needs saying differently.
6. **IP addresses in logs.** Render, Cloudflare and Supabase keep request logs with IP
   addresses. **Filled 2026-11-27 from the providers' own pages:** Render — 7 days on the
   Hobby workspace plan (Render's pricing table: "Log retention | 7 days | 14 days | 30
   days | 30 days", Hobby first; the logging page: "*Hobby* | 7 days"; HTTP request logs
   exist only on Pro and above; our server's own access log lines (uvicorn) carry a client
   address — whether the visitor's or Render's proxy was not checked).
   Supabase Free — API and database logs 1 day, Auth audit logs 24 hours. Cloudflare — no
   period stated: its privacy policy (effective 2025-11-04), section 11, says personal
   information is stored "for a period of time that is consistent with the business
   purposes". Still blank: TMDB and Google (their own policies), backups. These follow
   the plans: a move to a paid workspace or a Supabase Pro plan changes them.
   Sources (read 2026-11-27): https://render.com/pricing, https://render.com/docs/logging,
   https://supabase.com/pricing, https://supabase.com/docs/guides/telemetry/logs,
   https://www.cloudflare.com/privacypolicy/.
7. **TMDB attribution** must be on the About screen (`docs/legal.md` §1). It is in the
   terms.
8. **A conflict to note.** `CLAUDE.md` says the TMDB commercial licence is needed "before
   public launch". `docs/legal.md` and ADR 0002 say it is needed before the product earns
   money (a free launch is non-commercial). The lawyer or the user decides which applies.
   The TMDB email asks TMDB directly.
