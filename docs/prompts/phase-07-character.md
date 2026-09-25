# Phase 7 — Character Match

Read `CLAUDE.md` and **`docs/legal.md`** first. Phase 6's gate must be green.

This feature carries legal risk. The constraints below are not style preferences.

## Hard constraints

- **Text names only.** No character images, artwork, logos, silhouettes, stylised icons or
  AI-generated likenesses. Anywhere: app, share cards, store listing, marketing.
- A visible disclaimer on every result screen: entertainment only, unofficial, not a
  psychological assessment.
- Public-domain characters (Sherlock Holmes and similar) weighted higher in the first
  version.
- The feature does not go to production until a lawyer has reviewed it.

If a task in this phase conflicts with these constraints, stop and say so.

## Goal

A user gets a character similarity result derived from their taste, with a route back into
recommendations.

## Build

1. **Character catalogue** — `app/pipelines/characters.py`
   - Seed from the `character_name` field on `credits`, top 2,000–3,000 by the popularity
     of the films they appear in.
   - Clean: drop empty, duplicate, "uncredited", "voice", and single-scene roles.
   - `characters` table: name, source film ids, public_domain flag, trait vector.
2. **Character traits** — 11 dimensions (strategic, independence, curiosity, leadership,
   risk-taking, problem-solving, teamwork, loyalty, adaptability, humor, ambition).
   Define them in `packages/shared/character_traits.json`, mirrored in Python, exactly the
   way film traits are handled. Extract with Haiku, validate, never default silently.
3. **Quiz** — 12 questions, 4 options each, skippable. `character_quiz_answers` table.
4. **Character DNA** — `app/services/character.py`
   - Combine the film taste vector and, if present, the quiz answers into an 11-dimension
     vector. Weight the quiz higher when it exists.
   - Match by cosine similarity. Return top 4.
   - Generate the "why" from the real dimension overlap, cached like film explanations.
5. **Character → films** — reuse `app/services/recommend.py`, seeded by the character's
   film trait profile. This is the feature's actual value; do not skip it.
6. **Share card** — server-rendered image, **text and trait bars only**, no likeness.
7. **UI** — quiz, result, and the entry point on the DNA screen, on web and mobile.

## Required tests

- `test_character_ingest.py` — junk roles are dropped; duplicates merged; the
  public_domain flag is set for a known fixture list
- `test_character_traits_parsing.py` — same validation rules as film traits: missing key
  raises, out of range raises, no silent defaults
- `test_character_dna.py` — taste-only path produces a vector; quiz answers shift it in the
  expected direction; a skipped question is neutral, not zero
- `test_character_matching.py` — hand-computed example matches the returned percentage;
  public-domain characters rank higher at equal similarity
- `test_character_to_movies.py` — the returned films come from the recommendation service
  and exclude already-rated films
- `test_no_images.py` — **no character record, API response or share-card payload contains
  an image URL or binary field.** Assert on the serialised response.
- `test_disclaimer_present.py` — the result payload always carries the disclaimer string;
  it cannot be disabled by any parameter
- `CharacterResult.test.tsx` / `character_result_test.dart` — the disclaimer renders and is
  not clipped; no `<img>` in the rendered result

## Gate — do not skip

```bash
cd services/api && ruff check . && ruff format --check . && pytest -q --cov=app --cov-report=term-missing
cd apps/web && npm run lint && npm run typecheck && npm test
cd apps/mobile && flutter analyze && flutter test
```

Pass condition: **all pass; coverage of `app/services/character.py` at least 85%;
`test_no_images.py` and `test_disclaimer_present.py` pass with their assertions intact.**

Manual checklist:
- [ ] Take the quiz yourself and with 5 other people. Do the results feel plausible?
- [ ] Review the top 200 characters by hand. Flag any that should not be there.
- [ ] Confirm by inspection that no image of any character exists anywhere in the app,
      the share card, or the store assets.
- [ ] **Lawyer review completed and its outcome recorded in `docs/legal.md`.**
      Without this, the feature stays behind a flag.

## Report

1. Gate output and coverage.
2. The 6 quiz results and whether they seemed right.
3. The legal review outcome.
4. Do not start Phase 8.
