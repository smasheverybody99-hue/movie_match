# Phase 5 — Closed alpha

This phase is different: **you write very little code.** The work is measurement and
listening. Phase 4's gate must be green.

Read `docs/TZ.md` sections 7 and 8, and the roadmap's F5 gate.

## Goal

Find out whether the product's core claim is true before spending three weeks on a mobile
app: **do people actually watch what Movie Match recommends?**

## Build

1. **Telemetry** — `app/services/events.py`, table `events`
   - Record: `recommendation_shown`, `recommendation_clicked`, `added_to_watchlist`,
     `marked_watched`, `rated`, `assistant_query`, `onboarding_step`, `onboarding_done`.
   - Every event carries user id, timestamp, and the relevant film id. No personal content.
   - The web client sends them in batches, not one request per event.
2. **Metrics query** — `app/pipelines/metrics.py`
   - A command printing, for a date range:
     - recommendation → watched within 7 days (**the gate metric**)
     - onboarding completion rate
     - ratings per user in week 1
     - assistant queries per user
     - D1 / D7 return rate
3. **Feedback path**
   - A "this recommendation was wrong" control on each card, storing the film and an
     optional reason. This is data, not support.
4. **Nothing else.** Do not add features this phase. Bugs testers hit get fixed; new
   ideas go to the backlog in `docs/TZ.md` section 2.

## Required tests

- `test_events.py` — each event type is recorded with the right shape; batching writes all
  events in one transaction; malformed events are rejected, not silently dropped
- `test_metrics.py` — with a seeded fixture dataset whose correct answers you compute by
  hand, each metric returns exactly the expected number. Write the hand calculation in the
  test as a comment.
- `test_events_privacy.py` — no event payload contains free text the user typed

## Gate — do not skip

Two gates this phase. The technical one:

```bash
cd services/api && ruff check . && ruff format --check . && pytest -q --cov=app --cov-report=term-missing
cd apps/web && npm run lint && npm run typecheck && npm test
```

**The product gate** — this is the one that matters:

- [ ] 30–50 testers recruited and onboarded
- [ ] At least 2 weeks of data collected
- [ ] **Recommendation → watched within 7 days is at least 15%**
- [ ] Onboarding completion is at least 70%
- [ ] At least 10 user interviews of 20 minutes each, notes written up in
      `docs/research/alpha-interviews.md`

If the 15% metric is not met: **stop. Do not start Phase 6.** Go back to Phase 2 and
rework the engine — the most likely causes are the trait definitions, the weighting, or
the diversification. Re-run the alpha afterwards. Building a mobile app on a recommender
that does not work wastes three weeks.

## Report

1. The metrics table.
2. The five most common things testers said, in their words.
3. Your recommendation: proceed, or rework the engine. Say which and why.
