"""A hand-made alpha for the metrics tests: four testers and one user who is not.

The unit test computes from these rows directly; the integration test stores them and
reads them back. The expected numbers, worked out by hand, are in tests/unit/test_metrics.py.

Range: 2026-11-23 00:00 to 2026-12-07 00:00 UTC, as of 2026-12-07 00:00 UTC.
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.pipelines.metrics import Feedback, Row, Tester

START = datetime(2026, 11, 23, tzinfo=UTC)
END = datetime(2026, 12, 7, tzinfo=UTC)
AS_OF = END

U1, U2, U3, U4, OUTSIDER = (uuid.UUID(int=n) for n in (1, 2, 3, 4, 9))


def at(day: int, hour: int, minute: int = 0) -> datetime:
    """`day` of November 2026 (31 = 1 December, ...)."""
    return datetime(2026, 11, 1, hour, minute, tzinfo=UTC) + timedelta(days=day - 1)


TESTERS = [
    Tester(U1, at(23, 10)),
    Tester(U2, at(23, 12)),
    Tester(U3, at(24, 9)),
    Tester(U4, at(35, 9)),  # 5 December: joined late, every window still open
]
OUTSIDER_SINCE = at(23, 8)


def _ratings(user: uuid.UUID, films: range, day: int, hour: int, first_minute: int) -> list[Row]:
    return [
        Row(user, "rated", film, at(day, hour, first_minute + i)) for i, film in enumerate(films)
    ]


ROWS: list[Row] = [
    # U1: onboards, ten ratings; 201 shown twice and marked watched in time; 202 rated one
    # hour after its window; 203 (assistant) rated the same evening; three assistant
    # queries, a fourth after the range.
    Row(U1, "onboarding_step", None, at(23, 10, 5)),
    *_ratings(U1, range(101, 111), 23, 10, 6),
    Row(U1, "onboarding_done", None, at(23, 10, 20)),
    Row(U1, "recommendation_shown", 201, at(23, 11)),
    Row(U1, "recommendation_shown", 202, at(23, 11)),
    Row(U1, "recommendation_shown", 201, at(24, 14)),
    Row(U1, "recommendation_clicked", 201, at(24, 14, 1)),
    Row(U1, "marked_watched", 201, at(26, 20)),
    Row(U1, "rated", 202, at(30, 12)),
    Row(U1, "recommendation_shown", 203, at(25, 15)),
    Row(U1, "rated", 203, at(25, 22)),
    Row(U1, "assistant_query", None, at(25, 16)),
    Row(U1, "assistant_query", None, at(25, 16, 5)),
    Row(U1, "assistant_query", None, at(25, 16, 10)),
    Row(U1, "assistant_query", None, at(37, 1)),  # 7 December 01:00, after the range
    # U2: starts onboarding, rates four, never finishes; 204 shown and not watched; 205
    # shown on 1 December, its window still open.
    Row(U2, "onboarding_step", None, at(23, 12, 5)),
    *_ratings(U2, range(111, 115), 23, 12, 10),
    Row(U2, "recommendation_shown", 204, at(28, 9)),
    Row(U2, "recommendation_shown", 205, at(31, 9)),
    # U3: twelve ratings and a re-rating of one of them; 206 saved, watched and rated in
    # time; 127 rated an hour after week 1; one assistant query.
    *_ratings(U3, range(115, 127), 24, 9, 10),
    Row(U3, "onboarding_done", None, at(24, 9, 30)),
    Row(U3, "rated", 115, at(25, 8)),
    Row(U3, "recommendation_shown", 206, at(25, 10)),
    Row(U3, "added_to_watchlist", 206, at(25, 10, 1)),
    Row(U3, "marked_watched", 206, at(27, 20)),
    Row(U3, "rated", 206, at(27, 21)),
    Row(U3, "assistant_query", None, at(26, 12)),
    Row(U3, "rated", 127, at(31, 10)),
    # U4: joined 5 December, onboarded, 207 shown, one query.
    *_ratings(U4, range(128, 138), 35, 9, 10),
    Row(U4, "onboarding_done", None, at(35, 9, 30)),
    Row(U4, "recommendation_shown", 207, at(35, 10)),
    Row(U4, "assistant_query", None, at(36, 12)),
    # Not a tester: shown, watched, onboarded - none of it may count.
    Row(OUTSIDER, "onboarding_done", None, at(23, 9)),
    Row(OUTSIDER, "recommendation_shown", 208, at(23, 9, 30)),
    Row(OUTSIDER, "marked_watched", 208, at(24, 9)),
    Row(OUTSIDER, "assistant_query", None, at(24, 10)),
]

FEEDBACK = [
    Feedback(U1, 202, "not_my_genre", at(23, 11, 2)),
    Feedback(U2, 204, None, at(28, 9, 1)),
    Feedback(OUTSIDER, 208, "seen", at(23, 9, 31)),
]

FILMS = sorted({r.movie_id for r in ROWS if r.movie_id is not None})
