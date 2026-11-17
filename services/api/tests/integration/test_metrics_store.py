"""The metrics read from the database: the hand-made alpha (tests/metrics_dataset.py)
stored as rows, read back by `collect`, gives the numbers worked out by hand in
tests/unit/test_metrics.py."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, RecommendationFeedback, User
from app.pipelines.metrics import collect, compute
from tests.integration.api import seed_films
from tests.metrics_dataset import (
    AS_OF,
    END,
    FEEDBACK,
    FILMS,
    OUTSIDER,
    OUTSIDER_SINCE,
    ROWS,
    START,
    TESTERS,
    at,
)


async def _store(session: AsyncSession) -> None:
    await seed_films(session, dict.fromkeys(FILMS))
    for tester in TESTERS:
        session.add(User(id=tester.id, created_at=tester.created_at, alpha_tester=True))
    session.add(User(id=OUTSIDER, created_at=OUTSIDER_SINCE, alpha_tester=False))
    await session.flush()
    for row in ROWS:
        session.add(
            Event(user_id=row.user_id, type=row.type, movie_id=row.movie_id, occurred_at=row.at)
        )
    # An event after the report's moment: a report made later must not change.
    session.add(Event(user_id=TESTERS[1].id, type="rated", movie_id=204, occurred_at=at(37, 2)))
    for press in FEEDBACK:
        session.add(
            RecommendationFeedback(
                user_id=press.user_id,
                movie_id=press.movie_id,
                source="for_you",
                reason=press.reason,
                created_at=press.at,
                updated_at=press.at,
            )
        )
    await session.commit()


async def test_collect_reads_the_testers_and_their_events(db_session: AsyncSession) -> None:
    await _store(db_session)
    testers, rows, feedback = await collect(db_session, AS_OF)
    # Other tests' users never have alpha_tester set, so these four are all there is.
    assert {t.id for t in testers} == {t.id for t in TESTERS}
    # Not the outsider's, nor the two after the report's moment (U1's query, U2's rating).
    assert len(rows) == len([r for r in ROWS if r.user_id != OUTSIDER and r.at <= AS_OF])
    report = compute(testers, rows, feedback, START, END, AS_OF)
    assert (report.watched.either.hits, report.watched.either.total) == (3, 5)
    assert (report.onboarding.hits, report.onboarding.total) == (3, 4)
    assert report.queries == 5
    assert (report.d1.hits, report.d1.total, report.d7.hits) == (2, 3, 3)
    assert report.feedback == {"not_my_genre": 1, None: 1}


async def test_all_users_takes_in_the_rest(db_session: AsyncSession) -> None:
    await _store(db_session)
    testers, rows, _ = await collect(db_session, AS_OF, all_users=True)
    assert OUTSIDER in {t.id for t in testers}
    assert any(r.user_id == OUTSIDER for r in rows)
