"""The closed alpha's numbers (Phase 5), for a date range.

    python -m app.pipelines.metrics --from 2026-11-23 --to 2026-12-06
    python -m app.pipelines.metrics --from 2026-11-23 --to 2026-12-06 --as-of 2026-12-07T00:00Z

Read-only. Counts only users with `users.alpha_tester` set (user decision, 2026-11-17),
unless `--all-users`. Events after `--as-of` (default: now) are ignored, so a report can be
made again later with the same answer.

Definitions (docs/prompts/phase-05-alpha.md; decisions of 2026-11-17):

* **Recommendation -> watched within 7 days** (the gate metric). A recommendation is a
  (user, film) pair, at its first `recommendation_shown`; shown again it is the same one.
  It counts when it was first shown in the range and its 7 days have closed by `as-of`
  (TZ 1.31); the rest are reported as still open. Watched: a `marked_watched` or a `rated`
  for that film from the first showing to 7 days after it. Reported for either, and for
  each on its own.
* **Onboarding completion**: users with `onboarding_done`, out of all counted users.
* **Ratings per user in week 1**: distinct films rated in the 7 days from the user's
  `created_at`, over the users whose week 1 has closed.
* **Assistant queries per user**: `assistant_query` events in the range, over all counted
  users.
* **D1 / D7 return**: any event in the 24 hours starting 1 (7) days after `created_at`,
  over the users for whom that day has passed.

Shares carry a 95% Wilson interval: twelve testers are not proof (phase-05 prompt).
"""

import argparse
import asyncio
import math
import statistics
import uuid
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, RecommendationFeedback, User
from app.pipelines.db import job_session

WINDOW = timedelta(days=7)
DAY = timedelta(days=1)
Z95 = 1.96
WATCHED = ("marked_watched", "rated")


@dataclass(frozen=True)
class Tester:
    id: uuid.UUID
    created_at: datetime


@dataclass(frozen=True)
class Row:
    user_id: uuid.UUID
    type: str
    movie_id: int | None
    at: datetime


@dataclass(frozen=True)
class Feedback:
    user_id: uuid.UUID
    movie_id: int
    reason: str | None
    at: datetime


@dataclass(frozen=True)
class Share:
    hits: int
    total: int

    @property
    def value(self) -> float | None:
        return self.hits / self.total if self.total else None

    def interval(self) -> tuple[float, float] | None:
        """The 95% Wilson score interval; None with nothing counted."""
        if not self.total:
            return None
        n, p, z2 = self.total, self.hits / self.total, Z95 * Z95
        centre = (p + z2 / (2 * n)) / (1 + z2 / n)
        half = Z95 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
        return max(centre - half, 0.0), min(centre + half, 1.0)


@dataclass(frozen=True)
class Watched:
    either: Share
    marked: Share
    rated: Share
    still_open: int


@dataclass(frozen=True)
class WeekOne:
    mean: float | None
    median: float | None
    users: int


@dataclass(frozen=True)
class Report:
    start: datetime
    end: datetime
    as_of: datetime
    users: int
    watched: Watched
    onboarding: Share
    week_one: WeekOne
    queries: int
    queries_per_user: float | None
    d1: Share
    d7: Share
    feedback: dict[str | None, int]


def _first_shown(rows: Iterable[Row]) -> dict[tuple[uuid.UUID, int], datetime]:
    first: dict[tuple[uuid.UUID, int], datetime] = {}
    for row in rows:
        if row.type == "recommendation_shown" and row.movie_id is not None:
            key = (row.user_id, row.movie_id)
            if key not in first or row.at < first[key]:
                first[key] = row.at
    return first


def watched_within_7_days(
    rows: Sequence[Row], start: datetime, end: datetime, as_of: datetime
) -> Watched:
    watches: dict[tuple[uuid.UUID, int], list[Row]] = defaultdict(list)
    for row in rows:
        if row.type in WATCHED and row.movie_id is not None:
            watches[(row.user_id, row.movie_id)].append(row)
    counted = still_open = either = marked = rated = 0
    for key, shown in _first_shown(rows).items():
        if not start <= shown < end:
            continue
        if shown + WINDOW > as_of:
            still_open += 1
            continue
        counted += 1
        kinds = {w.type for w in watches.get(key, []) if shown <= w.at <= shown + WINDOW}
        either += bool(kinds)
        marked += "marked_watched" in kinds
        rated += "rated" in kinds
    return Watched(
        either=Share(either, counted),
        marked=Share(marked, counted),
        rated=Share(rated, counted),
        still_open=still_open,
    )


def onboarding_completion(testers: Sequence[Tester], rows: Sequence[Row]) -> Share:
    done = {r.user_id for r in rows if r.type == "onboarding_done"}
    return Share(sum(t.id in done for t in testers), len(testers))


def ratings_in_week_one(testers: Sequence[Tester], rows: Sequence[Row], as_of: datetime) -> WeekOne:
    counts = []
    for tester in testers:
        week_end = tester.created_at + WINDOW
        if week_end > as_of:
            continue
        films = {
            r.movie_id
            for r in rows
            if r.user_id == tester.id and r.type == "rated" and tester.created_at <= r.at < week_end
        }
        counts.append(len(films))
    if not counts:
        return WeekOne(None, None, 0)
    return WeekOne(statistics.mean(counts), statistics.median(counts), len(counts))


def assistant_queries(
    testers: Sequence[Tester], rows: Sequence[Row], start: datetime, end: datetime
) -> tuple[int, float | None]:
    ids = {t.id for t in testers}
    total = sum(
        1 for r in rows if r.type == "assistant_query" and r.user_id in ids and start <= r.at < end
    )
    return total, (total / len(testers) if testers else None)


def returned(testers: Sequence[Tester], rows: Sequence[Row], day: int, as_of: datetime) -> Share:
    """Users with any event in the 24 hours from `day` days after they signed up."""
    by_user: dict[uuid.UUID, list[datetime]] = defaultdict(list)
    for row in rows:
        by_user[row.user_id].append(row.at)
    hits = total = 0
    for tester in testers:
        opens = tester.created_at + day * DAY
        if opens + DAY > as_of:
            continue
        total += 1
        hits += any(opens <= at < opens + DAY for at in by_user[tester.id])
    return Share(hits, total)


def feedback_reasons(
    feedback: Sequence[Feedback], start: datetime, end: datetime
) -> dict[str | None, int]:
    return dict(Counter(f.reason for f in feedback if start <= f.at < end))


def compute(
    testers: Sequence[Tester],
    rows: Sequence[Row],
    feedback: Sequence[Feedback],
    start: datetime,
    end: datetime,
    as_of: datetime,
) -> Report:
    """Every number, from rows already limited to the counted users."""
    ids = {t.id for t in testers}
    rows = [r for r in rows if r.user_id in ids and r.at <= as_of]
    feedback = [f for f in feedback if f.user_id in ids]
    queries, per_user = assistant_queries(testers, rows, start, end)
    return Report(
        start=start,
        end=end,
        as_of=as_of,
        users=len(testers),
        watched=watched_within_7_days(rows, start, end, as_of),
        onboarding=onboarding_completion(testers, rows),
        week_one=ratings_in_week_one(testers, rows, as_of),
        queries=queries,
        queries_per_user=per_user,
        d1=returned(testers, rows, 1, as_of),
        d7=returned(testers, rows, 7, as_of),
        feedback=feedback_reasons(feedback, start, end),
    )


# --- output -----------------------------------------------------------------------------


def _share(share: Share) -> str:
    if not share.total:
        return f"{share.hits}/0  (nothing to count yet)"
    low, high = share.interval() or (0.0, 0.0)
    return f"{share.hits}/{share.total} = {share.value:.1%}  (95% CI {low:.0%}-{high:.0%})"


def _number(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def format_report(report: Report) -> str:
    w = report.watched
    reasons = ", ".join(
        f"{reason or 'no reason'}: {count}"
        for reason, count in sorted(report.feedback.items(), key=lambda kv: (-kv[1], kv[0] or ""))
    )
    lines = [
        f"range {report.start:%Y-%m-%d %H:%M} - {report.end:%Y-%m-%d %H:%M} UTC, "
        f"as of {report.as_of:%Y-%m-%d %H:%M} UTC, {report.users} users",
        "",
        f"recommendation -> watched in 7 days  {_share(w.either)}",
        f"  by 'watched'                       {_share(w.marked)}",
        f"  by a rating                        {_share(w.rated)}",
        f"  shown, 7 days not over yet         {w.still_open}",
        f"onboarding completion                {_share(report.onboarding)}",
        f"ratings per user in week 1           mean {_number(report.week_one.mean)}, "
        f"median {_number(report.week_one.median)}, over {report.week_one.users} users",
        f"assistant queries per user           {_number(report.queries_per_user)} "
        f"({report.queries} in all)",
        f"D1 return                            {_share(report.d1)}",
        f"D7 return                            {_share(report.d7)}",
        f"'wrong' presses                      {sum(report.feedback.values())}"
        + (f"  ({reasons})" if reasons else ""),
    ]
    return "\n".join(lines)


# --- the database -----------------------------------------------------------------------


async def collect(
    session: AsyncSession, as_of: datetime, *, all_users: bool = False
) -> tuple[list[Tester], list[Row], list[Feedback]]:
    """The counted users, their events up to `as_of` and their "wrong" presses."""
    users = select(User.id, User.created_at)
    if not all_users:
        users = users.where(User.alpha_tester.is_(True))
    testers = [Tester(u.id, u.created_at) for u in (await session.execute(users)).all()]
    ids = [t.id for t in testers]
    if not ids:
        return [], [], []
    events = await session.execute(
        select(Event.user_id, Event.type, Event.movie_id, Event.occurred_at).where(
            Event.user_id.in_(ids), Event.occurred_at <= as_of
        )
    )
    presses = await session.execute(
        select(
            RecommendationFeedback.user_id,
            RecommendationFeedback.movie_id,
            RecommendationFeedback.reason,
            RecommendationFeedback.updated_at,
        ).where(RecommendationFeedback.user_id.in_(ids))
    )
    return (
        testers,
        [Row(*row) for row in events.all()],
        [Feedback(*row) for row in presses.all()],
    )


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time(0), tzinfo=UTC)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="The closed alpha's metrics (read-only).")
    parser.add_argument("--from", dest="start", type=date.fromisoformat, required=True)
    parser.add_argument("--to", dest="to", type=date.fromisoformat, required=True, help="inclusive")
    parser.add_argument("--as-of", dest="as_of", type=datetime.fromisoformat, default=None)
    parser.add_argument("--all-users", action="store_true", help="not only alpha testers")
    args = parser.parse_args(argv)
    if args.to < args.start:
        parser.error("--to is before --from")
    if args.as_of is not None and args.as_of.tzinfo is None:
        parser.error("--as-of needs a time zone, e.g. 2026-12-07T00:00Z")
    return args


async def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    start, end = _day_start(args.start), _day_start(args.to) + DAY
    as_of = args.as_of or datetime.now(UTC)
    async with job_session() as session:
        testers, rows, feedback = await collect(session, as_of, all_users=args.all_users)
    print(format_report(compute(testers, rows, feedback, start, end, as_of)))


if __name__ == "__main__":
    asyncio.run(main())
