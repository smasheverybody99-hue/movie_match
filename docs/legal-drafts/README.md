# Legal drafts: for the lawyer's review, not published

Written 2026-11-23 by Claude, on the user's request. **Not legal advice and not final.**
Nothing here is live in the app.

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
  - AI: Google Gemini API.
  - Images: loaded from TMDB's servers.
- **Deleting an account** (`DELETE /me`) removes every app row belonging to the user
  (ON DELETE CASCADE).

## Gaps the lawyer and the user must see (not fixed)

1. **The sign-in record survives account deletion.** `services/users.py` says the Supabase
   Auth identity, which holds the email, is not touched. The policy promises full
   deletion, so before launch either the code removes the Auth user too, or the policy
   says otherwise.
2. **There is no data export.** `docs/legal.md` §3 says export "must actually work". The
   drafts promise it on request by email, done by hand, until a feature exists.
3. **Data localisation (Uzbekistan).** The Law on Personal Data (No. ZRU-547), as
   amended in 2021, is understood to require that personal data of citizens of
   Uzbekistan be processed and stored on servers located in Uzbekistan. Our database is in
   Singapore. **The lawyer must check this first:** it can change where the database
   must live, not just the text.
4. **Minimum age.** Left blank for the lawyer: 13, 16 or 18 depending on the law the
   lawyer applies.
5. **The alpha's free-tier exception** (ADR 0004). During the closed alpha, Google may use
   what the assistant is sent. The public-launch policy assumes the paid tier. The alpha
   paragraph is marked and is removed at launch.
6. **IP addresses in logs.** Render, Cloudflare and Supabase keep request logs with IP
   addresses. Retention is set by each provider and left blank.
7. **TMDB attribution** must be on the About screen (`docs/legal.md` §1). It is in the
   terms.
8. **A conflict to note.** `CLAUDE.md` says the TMDB commercial licence is needed "before
   public launch". `docs/legal.md` and ADR 0002 say it is needed before the product earns
   money (a free launch is non-commercial). The lawyer or the user decides which applies.
   The TMDB email asks TMDB directly.
9. **Who is named if the app is published from someone else's Play account** (TZ 1.39,
   option B, decision pending). In option B a trusted person (a parent or relative) owns
   the Google Play developer account and invites the user as Admin; the store page then
   shows that person as the developer. Questions for the lawyer:
   - In the privacy policy and the terms, who is the operator / data controller and the
     contact: the account owner, the user who builds and runs the service, or both?
   - Must the name in the policy match the developer name Google shows on the store page?
   - After an app transfer to the user's own account later: what must change in the policy
     and terms, and must existing users be told?
