# ADR 0002 — Movie data source and licensing timing

Date: 2026-09-25 · Status: accepted · Supersedes the licensing timing in ADR 0001

## Context

TMDB's API is free for non-commercial use; a commercial product needs a licence
negotiated through sales@themoviedb.org. ADR 0001 and the original roadmap treated that
licence as a phase-0 task, on the assumption it gated everything.

We reconsidered whether openly licensed sources could remove the dependency entirely.

What the licences actually say:

- **Wikidata** — CC0. Commercial reuse is unrestricted. Covers titles, years, runtimes,
  directors, cast, genres.
- **MovieLens** — "may not use this information for any commercial or revenue-bearing
  purposes without first obtaining permission". Unusable for a commercial product.
- **IMDb datasets** — personal and non-commercial use only. Unusable.
- **Posters and stills** — copyrighted. Wikipedia hosts them as non-free fair use, which
  does not grant reuse rights. There is no open source of modern film posters.
- **Streaming availability** — no open source.

## Decision

Build on the **TMDB free tier** through development and the closed alpha, and treat the
commercial licence as a **monetization prerequisite**, not a build prerequisite.

The product earns no revenue until it monetizes. Until then the free tier's
non-commercial terms cover the work: development, the 30–50 person alpha, and a free
public launch with no revenue.

The data layer stays source-agnostic: `app/pipelines/tmdb.py` is the only module that
knows TMDB's field names, and `to_movie_fields()` is the translation boundary. Nothing
downstream is coupled to the source.

## Why not the open-data-only path

It removes the licence question but costs posters and streaming availability. The entire
UI is built on poster recognition — onboarding is a grid of posters, the feed is poster
cards. A film discovery product where users cannot recognise films by sight is a
materially worse product, and the redesign is not a small change.

Wikidata remains the documented fallback if TMDB licensing later proves unworkable.

## Consequence

- No licence negotiation blocks the build.
- **Before charging for anything** — subscriptions, ads, paid tiers — the commercial
  licence must be in place. This is a launch-gate item in phase 9, not a phase-0 item.
- Attribution is required on the free tier too, from the moment the app is public.
- If the licence later proves too expensive, the fallback is Wikidata for metadata plus a
  redesign that does not depend on posters. Keep the translation boundary clean so that
  stays possible.
