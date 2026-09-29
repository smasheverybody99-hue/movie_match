# ADR 0005 — Web framework: stay on Vite

Date: 2026-09-29 · Status: accepted · Follows up: ADR 0001 ("if movie pages need SEO,
migrate to Next.js — decide before F3 ends")

The Phase 3 prompt asks for this record as `0002-web-framework.md`; 0002 was already
taken by the data-source decision, so it is 0005.

## Context

ADR 0001 left one question open: do film pages need server rendering for search engines?
If yes, the web app moves to Next.js, and that move has to happen before screens are
written, not after.

What the product says about who sees a film page:

- **No guest mode** (TZ FR-1, design system "Welcome": "Mehmon sifatida ko'rish yo'q").
  Every screen after `/welcome` is behind sign-in.
- **The film page is personal.** Its top block is the match ring and "why you'll like
  this" (design system, film page), both computed for the signed-in user. A crawler has
  no taste vector, so what it would index is the part of the page that is least ours:
  title, year, overview, all copied from TMDB and already indexed on TMDB and IMDb.
- **The TMDB licence** covers display in the app, not republishing the catalogue as an
  SEO landing-page set. Doing that deliberately is a legal question, not a framework one
  (`docs/legal.md`).

## Decision

**Stay on Vite + React 19 + React Router.** The app is a client-rendered SPA behind
sign-in. No film page is server-rendered.

## Consequences

- One deployable static bundle (Vercel/Netlify/any CDN); no Node server to run or pay for
  beside the Python API.
- Supabase Auth runs entirely in the browser (`@supabase/supabase-js`), which is the
  documented SPA path; no cookie/session bridging between a Node server and the API.
- The acquisition page (what a stranger sees before signing up) is `/welcome`, a static
  route in the same bundle. If marketing later needs indexable pages, they are a small
  static site of their own, not a reason to server-render the product.
- **Revisit** only if the product adds public, non-personal pages meant for search:
  shared Movie DNA cards, public lists, or a guest mode. Any of those needs a new TZ
  version first (TZ §2: scope changes only through a new TZ version), and then a new ADR.

## Alternatives rejected

- **Next.js (App Router).** Buys SSR for pages a crawler cannot usefully see, at the
  price of a second server runtime, a rewrite of the Phase 0 scaffold, and splitting auth
  between server and browser.
- **Vite + a prerender plugin for `/movie/:id`.** 5,000 static pages of TMDB text, the
  same licence question as above, and stale the day the catalogue syncs.
