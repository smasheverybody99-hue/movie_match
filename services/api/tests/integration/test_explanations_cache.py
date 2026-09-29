"""Explanations: cached per (user, film, language), capped per day, never blocking.

The generator is a fake that counts its calls; no test reaches a real LLM.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Explanation, Rating
from app.services.taste import recompute_taste
from app.services.users import ensure_user
from app.traits import TRAIT_COUNT
from tests.conftest import requires_db, rolled_back_session
from tests.integration.api import api_client, auth, seed_catalogue

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]

HALF = TRAIT_COUNT // 2
LIKED = [80.0] * HALF + [20.0] * HALF
RATED = [9_600_000 + i for i in range(1, 11)]
TARGETS = [9_610_000 + i for i in range(1, 6)]
NOTHING_SHARED = 9_620_001  # every dimension under 50 for the film: no reason to give


class FakeExplainer:
    model = "fake-explainer"

    def __init__(self, answer: str = "Dark and twisty, the way you like it.") -> None:
        self.answer = answer
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer


class FailingExplainer(FakeExplainer):
    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        raise RuntimeError("model unavailable")


class SlowExplainer(FakeExplainer):
    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        await asyncio.sleep(3600)
        return self.answer


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def catalogue(migrated_test_db: None) -> AsyncIterator[AsyncSession]:
    async with rolled_back_session() as session:
        await seed_catalogue(
            session,
            [
                *({"id": m, "vector": LIKED} for m in RATED),
                *({"id": m, "vector": LIKED} for m in TARGETS),
                {"id": NOTHING_SHARED, "vector": [40.0] * TRAIT_COUNT},
            ],
        )
        yield session


async def _user(session: AsyncSession) -> uuid.UUID:
    """A fresh user with a taste profile (ten films rated 9)."""
    user_id = uuid.uuid4()
    await ensure_user(session, user_id)
    for movie_id in RATED:
        session.add(Rating(user_id=user_id, movie_id=movie_id, score=9.0, liked_aspects=[]))
    await session.flush()
    await recompute_taste(session, user_id)
    await session.commit()
    return user_id


async def _get(session: AsyncSession, user_id: uuid.UUID, movie_id: int, **kwargs) -> dict:
    lang = kwargs.pop("lang", "uz")
    async with api_client(session, **kwargs) as client:
        response = await client.get(
            f"/recommendations/{movie_id}/explanation?lang={lang}", headers=auth(user_id)
        )
    assert response.status_code == 200, response.text
    return response.json()


async def test_second_request_makes_no_llm_call(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    first = await _get(catalogue, me, TARGETS[0], explainer=fake)
    second = await _get(catalogue, me, TARGETS[0], explainer=fake)
    assert (
        first
        == second
        == {
            "movie_id": TARGETS[0],
            "lang": "uz",
            "text": "Dark and twisty, the way you like it.",
        }
    )
    assert len(fake.prompts) == 1


async def test_the_prompt_carries_the_real_reasons(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    await _get(catalogue, me, TARGETS[1], explainer=fake, lang="en")
    (prompt,) = fake.prompts
    assert "Film 9610002" in prompt
    assert "Psychological: the viewer's taste 80/100, this film 80/100" in prompt
    assert "English" in prompt


async def test_each_language_is_cached_separately(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    await _get(catalogue, me, TARGETS[0], explainer=fake, lang="uz")
    await _get(catalogue, me, TARGETS[0], explainer=fake, lang="en")
    await _get(catalogue, me, TARGETS[0], explainer=fake, lang="en")
    assert len(fake.prompts) == 2


async def test_cached_text_rides_along_with_recommendations(catalogue: AsyncSession) -> None:
    me = await _user(catalogue)
    await _get(catalogue, me, TARGETS[0], explainer=FakeExplainer())
    async with api_client(catalogue) as client:  # no generator at all
        body = (await client.get("/recommendations", headers=auth(me))).json()
    texts = {
        item["movie"]["id"]: item["explanation"]
        for section in body["sections"]
        for item in section["items"]
    }
    assert texts[TARGETS[0]] == "Dark and twisty, the way you like it."
    assert texts[TARGETS[1]] is None  # not generated yet; the list does not wait for it


@pytest.mark.parametrize("explainer_class", [FailingExplainer, SlowExplainer])
async def test_a_failure_returns_null_and_caches_nothing(
    catalogue: AsyncSession, explainer_class: type, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.explain.TIMEOUT_SECONDS", 0.05)
    me = await _user(catalogue)
    body = await _get(catalogue, me, TARGETS[2], explainer=explainer_class())
    assert body["text"] is None
    stored = await catalogue.scalar(
        select(func.count()).select_from(Explanation).where(Explanation.user_id == me)
    )
    assert stored == 0


async def test_an_overlong_answer_is_not_stored(catalogue: AsyncSession) -> None:
    me = await _user(catalogue)
    body = await _get(catalogue, me, TARGETS[2], explainer=FakeExplainer("word " * 200))
    assert body["text"] is None


async def test_nothing_shared_means_no_call(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    body = await _get(catalogue, me, NOTHING_SHARED, explainer=fake)
    assert body["text"] is None
    assert fake.prompts == []


async def test_the_daily_cap_stops_generation(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    cap = {"explanation_daily_calls_per_user": 2}
    for movie_id in TARGETS[:3]:
        await _get(catalogue, me, movie_id, explainer=fake, settings=cap)
    assert len(fake.prompts) == 2
    # the cached ones are still served
    assert (await _get(catalogue, me, TARGETS[0], explainer=fake, settings=cap))["text"]


async def test_without_a_generator_the_text_is_null(catalogue: AsyncSession) -> None:
    me = await _user(catalogue)
    assert (await _get(catalogue, me, TARGETS[3]))["text"] is None


async def test_a_user_without_taste_gets_null(catalogue: AsyncSession) -> None:
    fake = FakeExplainer()
    assert (await _get(catalogue, uuid.uuid4(), TARGETS[3], explainer=fake))["text"] is None
    assert fake.prompts == []


async def test_unknown_film_is_404(catalogue: AsyncSession) -> None:
    async with api_client(catalogue, explainer=FakeExplainer()) as client:
        response = await client.get("/recommendations/1/explanation", headers=auth(uuid.uuid4()))
    assert response.status_code == 404
