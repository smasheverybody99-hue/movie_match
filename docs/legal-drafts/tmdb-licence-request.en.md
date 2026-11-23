# Draft: commercial licence request to TMDB (not sent)

Written 2026-11-23. The user sends it, if they choose to. Address from `docs/legal.md` §1:
sales@themoviedb.org. Blanks are `[____]`.

Before sending:
- fill in the blanks;
- check the user counts;
- remove the sentence about future revenue if there is no such plan.

---

**To:** sales@themoviedb.org
**Subject:** Licence enquiry: Movie Match, a film recommendation app (web and Android)

Hello,

I am [____ name], [____ role] of [____ company or "an independent developer"] in
[____ country]. I am building Movie Match, a film recommendation service that uses the
TMDB API, and I would like to know which licence it needs before its public launch.

**What the product does.** People rate films they have seen. Movie Match then suggests
other films and explains the match, and an assistant answers questions about films.
There is a website ([____ website]) and an Android app, which will be on Google Play.

**How we use TMDB:**
- **Metadata:** title, overview, release date, runtime, genres, keywords, and director
  and cast names, for a catalogue of about [____ 5,000] films. A background job fetches
  and refreshes it; it is never fetched inside a user's request.
- **Images:** posters and backdrops load from image.tmdb.org at TMDB's standard sizes. We
  do not store or redistribute the image files.
- **Derived data:** we compute our own scores for each film on 14 taste dimensions from
  this metadata. The film's text is sent to an AI model (Google Gemini) to produce those
  scores.
- **Attribution:** the TMDB logo and the notice "This product uses the TMDB API but is
  not endorsed or certified by TMDB" appear on the About screen.
- **Not used:** watch-provider (JustWatch) data, and TMDB user or account data.

**Scale and timeline:**
- A closed test with about [____ 15] testers runs from [____ 2026-11-29] to
  [____ 2026-12-13].
- The public web launch is planned for [____ 2026-12-15], and the Google Play release
  for late December 2026.
- We expect about [____] monthly active users in the first months.

**Money.** At launch the service is free: no ads, no subscriptions and no paid features.
[____ Optional: We may add paid features later, no earlier than [____].]

My questions:
1. Is a free public launch, as described, covered by the non-commercial terms of use, or
   does it already need a commercial licence?
2. If a commercial licence is needed now or later, what are the terms and the price for
   a product of this size?
3. Does sending film overviews to an AI model to compute our own scores, and storing those
   scores, comply with your terms? If not, what would make it comply?
4. Is there anything else in this use that we should change?

Thank you for your time. I am happy to give more details or a demo.

Kind regards,
[____ name]
[____ company]
[____ email] · [____ website]
