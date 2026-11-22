"""The alpha's data notice (ADR 0004, free-tier exception): GET /me says whether it is
needed and when it was accepted; POST /me/data-notice accepts it, once."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api import api_client, auth


async def test_accepting_is_recorded_and_the_first_time_stays(db_session: AsyncSession) -> None:
    me = auth(uuid.uuid4())
    async with api_client(db_session) as client:
        before = (await client.get("/me", headers=me)).json()
        first = await client.post("/me/data-notice", headers=me)
        accepted = (await client.get("/me", headers=me)).json()
        again = await client.post("/me/data-notice", headers=me)
        later = (await client.get("/me", headers=me)).json()
    assert before["data_notice_required"] is True
    assert before["data_notice_accepted_at"] is None
    assert (first.status_code, again.status_code) == (204, 204)
    assert accepted["data_notice_accepted_at"] is not None
    assert later["data_notice_accepted_at"] == accepted["data_notice_accepted_at"]


async def test_on_the_paid_tier_no_notice_is_needed(db_session: AsyncSession) -> None:
    async with api_client(db_session, settings={"data_notice_required": False}) as client:
        body = (await client.get("/me", headers=auth(uuid.uuid4()))).json()
    assert body["data_notice_required"] is False


async def test_one_users_acceptance_is_not_anothers(db_session: AsyncSession) -> None:
    me, other = auth(uuid.uuid4()), auth(uuid.uuid4())
    async with api_client(db_session) as client:
        await client.post("/me/data-notice", headers=me)
        theirs = (await client.get("/me", headers=other)).json()
    assert theirs["data_notice_accepted_at"] is None


async def test_missing_and_forged_tokens_are_401(db_session: AsyncSession) -> None:
    async with api_client(db_session) as client:
        missing = await client.post("/me/data-notice")
        forged = await client.post("/me/data-notice", headers=auth(uuid.uuid4(), forged=True))
    assert (missing.status_code, forged.status_code) == (401, 401)
