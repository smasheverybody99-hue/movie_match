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
from app.providers.base import Generated, Pricing, Usage
from app.services.taste import recompute_taste
from app.services.users import ensure_user
from app.traits import TRAIT_COUNT
from tests.conftest import requires_db, rolled_back_session
from tests.integration.api import api_client, auth, seed_catalogue

pytestmark = [requires_db, pytest.mark.asyncio(loop_scope="module")]

HALF = TRAIT_COUNT // 2
LIKED = [80.0] * HALF + [20.0] * HALF  # what the user rates 9, so their taste lands here
# The one rule measures the distance between taste and film against the catalogue spread
# (TZ 1.27), so the catalogue needs a film in each of the rule's three bands. The ordinary
# films give the catalogue its spread: sd ~ 15.4 per trait, and this taste sits ~0.72 sd
# off the catalogue mean, which clears the lean guard (0.40) every reason needs.
AT_MY_LEVEL = [83.0] * HALF + [17.0] * HALF  # 3 points off the taste: 0.19 sd, a reason
MIDBAND = [90.0] * HALF + [10.0] * HALF  # 10 points off: 0.65 sd, nothing either way
AWAY = [55.0] * HALF + [45.0] * HALF  # 25 points the other way: 1.62 sd, a difference
RATED = [9_600_000 + i for i in range(1, 11)]
TARGETS = [9_610_000 + i for i in range(1, 6)]
NOTHING_SHARED = 9_620_001  # in the middle band: not at the taste's level, not away from it
DIFFERENT = 9_620_002  # far enough the other way to say how it differs
ORDINARY = [9_630_000 + i for i in range(1, 11)]


class FakeExplainer:
    provider = "fake"
    model = "fake-explainer"
    pricing = Pricing(1.0, 2.0, "test rates")

    def __init__(self, answer: str = "Dark and twisty, the way you like it.") -> None:
        self.answer = answer
        self.prompts: list[str] = []

    async def generate(self, system: str, prompt: str) -> Generated:
        self.prompts.append(prompt)
        return Generated(self.answer, Usage(requests=1, input_tokens=100, output_tokens=20))


class FailingExplainer(FakeExplainer):
    async def generate(self, system: str, prompt: str) -> Generated:
        self.prompts.append(prompt)
        raise RuntimeError("model unavailable")


class SlowExplainer(FakeExplainer):
    async def generate(self, system: str, prompt: str) -> Generated:
        self.prompts.append(prompt)
        await asyncio.sleep(3600)
        return Generated(self.answer, Usage())


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def catalogue(migrated_test_db: None) -> AsyncIterator[AsyncSession]:
    async with rolled_back_session() as session:
        await seed_catalogue(
            session,
            [
                *({"id": m, "vector": LIKED} for m in RATED),
                *({"id": m, "vector": AT_MY_LEVEL} for m in TARGETS),
                {"id": NOTHING_SHARED, "vector": MIDBAND},
                {"id": DIFFERENT, "vector": AWAY},
                *({"id": m, "vector": [50.0] * TRAIT_COUNT} for m in ORDINARY),
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
            "reason": None,  # a text and a reason never come together
        }
    )
    assert len(fake.prompts) == 1


async def test_the_prompt_carries_the_real_reasons(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    await _get(catalogue, me, TARGETS[1], explainer=fake, lang="en")
    (prompt,) = fake.prompts
    assert "Film 9610002" in prompt
    assert "Psychological: the viewer's taste 80/100, this film 83/100" in prompt
    assert "sits at this viewer's own level" in prompt  # the reason brief
    assert "English" in prompt


async def test_a_film_away_from_the_taste_is_briefed_as_a_difference(
    catalogue: AsyncSession,
) -> None:
    """The reported contradiction of 2026-10-15: a film the viewer's taste leans away from
    still read as "you'll like this". It is now described by how it differs, and the model
    is told not to recommend it."""
    me, fake = await _user(catalogue), FakeExplainer("Its pace is far slower.")
    body = await _get(catalogue, me, DIFFERENT, explainer=fake, lang="en")
    assert (body["text"], body["reason"]) == ("Its pace is far slower.", None)
    (prompt,) = fake.prompts
    assert "sits well away from this viewer's taste" in prompt
    assert "sits at this viewer's own level" not in prompt
    assert "Psychological: the viewer's taste 80/100, this film 55/100" in prompt


async def test_each_language_is_cached_separately(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    for lang in ("uz", "en", "en", "ru", "ru"):
        await _get(catalogue, me, TARGETS[0], explainer=fake, lang=lang)
    assert len(fake.prompts) == 3
    assert "Russian" in fake.prompts[2]


async def test_without_a_language_the_answer_is_english(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    async with api_client(catalogue, explainer=fake) as client:
        response = await client.get(f"/recommendations/{TARGETS[0]}/explanation", headers=auth(me))
    assert response.status_code == 200, response.text
    assert response.json()["lang"] == "en"
    assert fake.prompts[0].endswith("Write the sentences in English.")


async def test_cached_text_rides_along_with_recommendations(catalogue: AsyncSession) -> None:
    me = await _user(catalogue)
    await _get(catalogue, me, TARGETS[0], explainer=FakeExplainer(), lang="ru")

    async def texts(lang: str) -> dict[int, str | None]:
        async with api_client(catalogue) as client:  # no generator at all
            response = await client.get(f"/recommendations?lang={lang}", headers=auth(me))
        return {
            item["movie"]["id"]: item["explanation"]
            for section in response.json()["sections"]
            for item in section["items"]
        }

    in_russian = await texts("ru")
    assert in_russian[TARGETS[0]] == "Dark and twisty, the way you like it."
    assert in_russian[TARGETS[1]] is None  # not generated yet; the list does not wait for it
    assert (await texts("en"))[TARGETS[0]] is None  # cached per language


@pytest.mark.parametrize("explainer_class", [FailingExplainer, SlowExplainer])
async def test_a_failure_returns_null_and_caches_nothing(
    catalogue: AsyncSession, explainer_class: type, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.explain.TIMEOUT_SECONDS", 0.05)
    me = await _user(catalogue)
    body = await _get(catalogue, me, TARGETS[2], explainer=explainer_class())
    assert (body["text"], body["reason"]) == (None, "failed")
    stored = await catalogue.scalar(
        select(func.count()).select_from(Explanation).where(Explanation.user_id == me)
    )
    assert stored == 0


async def test_an_overlong_answer_is_not_stored(catalogue: AsyncSession) -> None:
    me = await _user(catalogue)
    body = await _get(catalogue, me, TARGETS[2], explainer=FakeExplainer("word " * 200))
    assert (body["text"], body["reason"]) == (None, "rejected")


async def test_nothing_shared_means_no_call(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    body = await _get(catalogue, me, NOTHING_SHARED, explainer=fake)
    assert (body["text"], body["reason"]) == (None, "nothing_named")
    assert fake.prompts == []


async def test_the_daily_cap_stops_generation(catalogue: AsyncSession) -> None:
    me, fake = await _user(catalogue), FakeExplainer()
    cap = {"explanation_daily_calls_per_user": 2}
    bodies = [await _get(catalogue, me, m, explainer=fake, settings=cap) for m in TARGETS[:3]]
    assert len(fake.prompts) == 2
    # The third is refused by the cap, and says so: the interface can tell the user that
    # today's explanations are used up instead of falling back silently.
    assert [b["reason"] for b in bodies] == [None, None, "daily_cap"]
    # the cached ones are still served
    assert (await _get(catalogue, me, TARGETS[0], explainer=fake, settings=cap))["text"]


async def test_without_a_generator_the_text_is_null(catalogue: AsyncSession) -> None:
    me = await _user(catalogue)
    body = await _get(catalogue, me, TARGETS[3])
    assert (body["text"], body["reason"]) == (None, "no_generator")


async def test_a_user_without_taste_gets_null(catalogue: AsyncSession) -> None:
    fake = FakeExplainer()
    body = await _get(catalogue, uuid.uuid4(), TARGETS[3], explainer=fake)
    assert (body["text"], body["reason"]) == (None, "no_taste")
    assert fake.prompts == []


async def test_unknown_film_is_404(catalogue: AsyncSession) -> None:
    async with api_client(catalogue, explainer=FakeExplainer()) as client:
        response = await client.get("/recommendations/1/explanation", headers=auth(uuid.uuid4()))
    assert response.status_code == 404
