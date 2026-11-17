"""The alpha metrics on a hand-made dataset (tests/metrics_dataset.py). Every expected
number is worked out by hand in the comment above its assertion.

Range 23 Nov 00:00 - 7 Dec 00:00 UTC, as of 7 Dec 00:00. Testers U1-U4; OUTSIDER is not
one and counts nowhere.
"""

import math

import pytest

from app.pipelines.metrics import (
    Share,
    compute,
    format_report,
    parse_args,
)
from tests.metrics_dataset import AS_OF, END, FEEDBACK, ROWS, START, TESTERS


@pytest.fixture(scope="module")
def report():
    return compute(TESTERS, ROWS, FEEDBACK, START, END, AS_OF)


def test_recommendation_to_watched_within_7_days(report) -> None:
    # Pairs at their first showing, inside the range:
    #   U1-201  23 Nov 11:00, window to 30 Nov 11:00: marked watched 26 Nov -> hit (watched)
    #           (shown again 24 Nov: the same pair, not a second one)
    #   U1-202  23 Nov 11:00, window to 30 Nov 11:00: rated 30 Nov 12:00 -> one hour late, miss
    #   U1-203  25 Nov 15:00, window to 2 Dec 15:00: rated 25 Nov 22:00 -> hit (rating)
    #   U2-204  28 Nov 09:00, window to 5 Dec 09:00: nothing -> miss
    #   U3-206  25 Nov 10:00, window to 2 Dec 10:00: watched 27 Nov and rated 27 Nov -> hit (both)
    #   U2-205  1 Dec 09:00, window to 8 Dec 09:00 > as of -> still open, not counted
    #   U4-207  5 Dec 10:00, window to 12 Dec -> still open, not counted
    #   OUTSIDER-208: not a tester.
    # Counted 5. Either: 201, 203, 206 = 3/5. Watched: 201, 206 = 2/5. Rating: 203, 206 = 2/5.
    w = report.watched
    assert (w.either.hits, w.either.total) == (3, 5)
    assert (w.marked.hits, w.marked.total) == (2, 5)
    assert (w.rated.hits, w.rated.total) == (2, 5)
    assert w.still_open == 2
    assert w.either.value == 0.6


def test_onboarding_completion(report) -> None:
    # onboarding_done: U1, U3, U4 (U2 only started). 3 of the 4 testers; OUTSIDER not counted.
    assert (report.onboarding.hits, report.onboarding.total) == (3, 4)


def test_ratings_per_user_in_week_one(report) -> None:
    # Week 1 closed by 7 Dec 00:00 for U1 (to 30 Nov 10:00), U2 (30 Nov 12:00), U3 (1 Dec 09:00);
    # not for U4 (to 12 Dec).
    #   U1: 101-110 (10) + 203 on 25 Nov = 11; 202 on 30 Nov 12:00 is after week 1.
    #   U2: 111-114 = 4.
    #   U3: 115-126 (12; 115 rated again on 25 Nov is the same film) + 206 on 27 Nov = 13;
    #       127 on 1 Dec 10:00 is an hour after week 1.
    # Mean (11 + 4 + 13) / 3 = 28 / 3; median 11; 3 users.
    assert report.week_one.users == 3
    assert report.week_one.mean == pytest.approx(28 / 3)
    assert report.week_one.median == 11


def test_assistant_queries_per_user(report) -> None:
    # In the range: U1 3 (the fourth is 7 Dec 01:00, after it), U2 0, U3 1, U4 1 = 5.
    # Over 4 testers: 1.25. OUTSIDER's query is not counted.
    assert report.queries == 5
    assert report.queries_per_user == 1.25


def test_d1_and_d7_return(report) -> None:
    # D1: the 24 hours from 1 day after sign-up, counted once they are over by 7 Dec 00:00.
    #   U1 24 Nov 10:00 - 25 Nov 10:00: shown 201 at 24 Nov 14:00 -> returned
    #   U2 24 Nov 12:00 - 25 Nov 12:00: nothing (next event 28 Nov) -> not
    #   U3 25 Nov 09:00 - 26 Nov 09:00: re-rated 115 at 25 Nov 08:00 is before it; shown 206
    #      at 25 Nov 10:00 -> returned
    #   U4 6 Dec 09:00 - 7 Dec 09:00: not over -> not counted
    #   D1 = 2/3.
    # D7: the 24 hours from 7 days after.
    #   U1 30 Nov 10:00 - 1 Dec 10:00: rated 202 at 30 Nov 12:00 -> returned
    #   U2 30 Nov 12:00 - 1 Dec 12:00: shown 205 at 1 Dec 09:00 -> returned
    #   U3 1 Dec 09:00 - 2 Dec 09:00: rated 127 at 1 Dec 10:00 -> returned
    #   U4 not over. D7 = 3/3.
    assert (report.d1.hits, report.d1.total) == (2, 3)
    assert (report.d7.hits, report.d7.total) == (3, 3)


def test_wrong_presses_by_reason(report) -> None:
    # U1 "not_my_genre", U2 no reason; OUTSIDER's "seen" is not counted.
    assert report.feedback == {"not_my_genre": 1, None: 1}


def test_the_interval_is_wilson() -> None:
    # The phase prompt's own example: 9 of 12 is 75%, 95% interval roughly 47-91%.
    # p = 0.75, n = 12, z^2/n = 3.8416/12 = 0.32013
    # centre = (0.75 + 0.16007) / 1.32013 = 0.68940
    # half = 1.96 * sqrt(0.015625 + 0.0066694) / 1.32013 = 1.96 * 0.149313 / 1.32013 = 0.22169
    low, high = Share(9, 12).interval() or (0, 0)
    assert (round(low, 3), round(high, 3)) == (0.468, 0.911)
    # 3 of 5: centre (0.6 + 0.38416) / 1.76832 = 0.55654,
    # half 1.96 * sqrt(0.048 + 0.038416) / 1.76832 = 0.32583
    low, high = Share(3, 5).interval() or (0, 0)
    assert (round(low, 3), round(high, 3)) == (0.231, 0.882)
    assert Share(0, 0).interval() is None and Share(0, 0).value is None
    assert Share(0, 4).interval()[0] == 0.0  # type: ignore[index]
    assert math.isclose(Share(4, 4).interval()[1], 1.0)  # type: ignore[index]


def test_the_report_reads(report) -> None:
    text = format_report(report)
    assert "recommendation -> watched in 7 days  3/5 = 60.0%  (95% CI 23%-88%)" in text
    assert "onboarding completion                3/4 = 75.0%" in text
    assert "mean 9.33, median 11.00, over 3 users" in text
    assert "1.25 (5 in all)" in text
    assert "'wrong' presses                      2  (no reason: 1, not_my_genre: 1)" in text


def test_an_empty_alpha_says_so() -> None:
    text = format_report(compute([], [], [], START, END, AS_OF))
    assert "0/0  (nothing to count yet)" in text
    assert "mean -, median -, over 0 users" in text


def test_arguments() -> None:
    args = parse_args(["--from", "2026-11-23", "--to", "2026-12-06"])
    assert (str(args.start), str(args.to), args.as_of, args.all_users) == (
        "2026-11-23",
        "2026-12-06",
        None,
        False,
    )
    with pytest.raises(SystemExit):
        parse_args(["--from", "2026-12-06", "--to", "2026-11-23"])
    with pytest.raises(SystemExit):
        parse_args(["--from", "2026-11-23", "--to", "2026-12-06", "--as-of", "2026-12-07T00:00"])
