# Phase 2 — Recommendation engine and user API

Read `CLAUDE.md` first. Phase 1's gate must be green, including the manual 50-film review.

## Before you start

Read:
- `docs/TZ.md` sections 4 (FR-1, FR-4, FR-5, FR-6) and the match formula
- `docs/architecture.md` — the "Match percentage" section
- `app/services/similarity.py` from Phase 1

## Goal

A complete API: a user can sign in, rate films, and get recommendations with a match
percentage and a plain-language reason.

## Build

1. **Auth wiring**
   - Finish `app/deps.py`; add a dependency that creates the local `users` row on first
     authenticated request (Supabase is the identity source, our table mirrors it).
   - `GET /me`, `DELETE /me` (account deletion: removes all rows for that user).

2. **User data endpoints** — `app/routers/ratings.py`, `app/routers/watchlist.py`
   - `POST /ratings`, `DELETE /ratings/{movie_id}`, `GET /ratings`
   - `GET /watchlist`, `POST /watchlist`, `DELETE /watchlist/{movie_id}`,
     `POST /watchlist/{movie_id}/watched`
   - Every endpoint requires auth and only ever touches the caller's own rows.

3. **Taste profile** — `app/services/taste.py`
   - Build the user taste vector: rating-weighted mean of rated films' trait vectors,
     with recent ratings weighted higher.
   - Compute per-dimension weights from how tightly the user's highly-rated films cluster
     on that dimension. A scattered dimension gets a low weight.
   - Recompute on every rating change. Store on `users`.

4. **Matching** — `app/services/matching.py`
   - Implement exactly the formula in `docs/architecture.md`. Do not invent a different one.
   - `match_percentage(taste, weights, movie_vector) -> int`
   - `top_reasons(taste, movie_vector, n=3) -> list[str]` — the trait keys that
     contributed most to a high score.

5. **Recommendations** — `app/services/recommend.py`, `app/routers/recommendations.py`
   - Retrieve candidates (pgvector ANN, ~300), apply hard filters, score with the match
     formula, then diversify with MMR.
   - Exclude rated, watched and dismissed films.
   - At most 2 films per director per section.
   - Drop anything below 60% match.
   - Build sections: "For you", "Because you loved {film}", "Under 90 minutes",
     "Outside your usual taste".
   - `GET /recommendations` returns the sections.

6. **Explanations** — `app/services/explain.py`
   - Generate with Haiku, from the actual top reasons — never a generic sentence.
   - Check the `explanations` table before every call. Never regenerate a cached one.
   - If generation fails, return the recommendation without an explanation. Never block.

7. **Cold start**
   - `GET /onboarding/films` — a popularity-and-genre-spread set of films to pick from.
   - Recommendations endpoint returns a clear "not enough data" response below 10 ratings,
     not an empty list.

## Out of scope

No UI. No assistant. No character features.

## Required tests

Unit (no DB, no network):
- `test_taste_vector.py` — known ratings produce the expected vector; recent ratings weigh
  more; a single rating does not produce extreme weights
- `test_taste_weights.py` — a dimension where the user's favourites are tightly clustered
  gets a high weight; a scattered one gets a low weight
- `test_matching.py` — identical vectors give 100; maximally different give 0; the value
  matches a hand-computed example (write the arithmetic in the test as a comment);
  weights actually change the result
- `test_top_reasons.py` — returns the dimensions that really drove the score, ordered
- `test_mmr.py` — diversification drops a near-duplicate in favour of a different film

Integration (test DB, seeded fixtures):
- `test_ratings_api.py` — create, update, delete; rating twice updates rather than
  duplicates; taste vector changes after a rating
- `test_watchlist_api.py` — add, list, mark watched, remove
- `test_recommendations.py` — sections are returned; nothing below 60%; rated films are
  excluded; the director cap holds; "not enough data" below 10 ratings
- `test_explanations_cache.py` — the second request for the same (user, film) makes no
  LLM call (assert on a mock call count)
- `test_auth.py` — every protected endpoint returns 401 without a token, 401 with a
  forged token, and 200 with a valid one
- `test_isolation.py` — user A cannot read or modify user B's ratings or watchlist
- `test_account_deletion.py` — after `DELETE /me`, no rows for that user remain

## Gate — do not skip

```bash
cd services/api && ruff check . && ruff format --check . && pytest -q --cov=app --cov-report=term-missing
```

Pass condition: **all tests pass; coverage of `app/services/` at least 85%; every
endpoint has at least one auth-failure test.**

Manual checklist:
- [ ] Rate 30 films as yourself through the API. Read the recommendations you get back.
      Would you watch them? Say so honestly — this is the product's core claim.
- [ ] Verify the match percentage of one recommendation by hand from the stored vectors.
      It must match the API's number exactly.
- [ ] Check that the explanation for 5 recommendations actually describes the trait
      overlap, rather than being generically positive.

## Report

1. Gate output and coverage.
2. Your honest verdict on the 30-rating test.
3. The hand-verified match calculation.
4. Do not start Phase 3.
