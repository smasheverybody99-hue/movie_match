# Phase 8 — Social features and polish

Read `CLAUDE.md` first. Phase 7's gate must be green, including the legal review.

## Goal

Finish the feature set and bring performance and accessibility up to the targets in
`docs/TZ.md` section 5. After this phase, no new features before launch.

## Build

1. **Smart Watchlist** — `app/services/watchlist_groups.py`
   - Group saved films with the trait vectors already stored. No new model, no LLM call.
   - Groups: Watch next, Challenging, Light, Under 90 min, Hidden gems.
   - "Watch next" ranks by match and by how long a film has sat unwatched.
2. **Group Match** — `app/services/group.py`
   - Create a session, join by link, combine 2–8 taste vectors.
   - Scoring is the minimum satisfaction across members, not the average — one person
     hating the film matters more than another loving it.
   - Sessions expire after 24 hours.
3. **Taste Twin — do not build.** It needs collaborative filtering over 1,000+ active
   users. Write a one-paragraph note in `docs/decisions/0003-taste-twin.md` explaining the
   condition under which it becomes possible, and leave the feature out of the UI.
4. **Performance**
   - Web: LCP < 2.5s, INP < 200ms on the film page.
   - API: p95 < 300ms, recommendations < 500ms.
   - Mobile: cold start < 2s in release mode.
   - Find the slow paths by measuring, not guessing. Report before and after numbers.
5. **Accessibility**
   - Contrast 4.5:1 everywhere, keyboard navigation complete on web, screen-reader labels
     on both platforms, 44px minimum touch targets.

## Required tests

- `test_watchlist_groups.py` — each group's membership rule, with fixture films whose
  correct grouping you state in the test; a film can appear in two groups; an empty group
  is omitted rather than shown empty
- `test_group_match.py` — minimum-satisfaction scoring, verified against a hand-computed
  example; a member with very different taste measurably lowers a film's score; expired
  sessions reject joins
- `test_group_limits.py` — a 9th member is rejected; a session with 1 member returns that
  member's own recommendations
- `a11y.test.tsx` — axe runs clean on every screen in the component test suite
- Performance assertions in CI: a test that fails if the recommendations endpoint exceeds
  500ms against the fixture dataset

## Gate — do not skip

```bash
cd services/api && ruff check . && ruff format --check . && pytest -q --cov=app --cov-report=term-missing
cd apps/web && npm run lint && npm run typecheck && npm run build && npm test
cd apps/mobile && flutter analyze && flutter test
```

Pass condition: **all pass; overall `app/services/` coverage at least 85%; zero axe
violations.**

Manual checklist:
- [ ] Lighthouse on 3 screens. Report LCP and INP for each; all must meet target.
- [ ] Load test: 500 concurrent users. Report p95 and error rate.
- [ ] Cold start measured on the slowest test device.
- [ ] Screen reader pass on one full flow, on web and on a phone.
- [ ] Group Match with 4 real people. Was the shortlist acceptable to all four?

## Report

1. Gate output and coverage.
2. Before/after performance numbers.
3. The Group Match trial result.
4. Do not start Phase 9.
