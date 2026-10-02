"""GET /movies (search with filters) and GET /movies/{id} (detail, optional auth)."""

import uuid
from datetime import date

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie
from app.services.matching import match_percentage, top_reasons, weights_vector
from app.services.reasons import load_rule
from app.traits import TRAIT_KEYS
from tests.integration.api import api_client, auth, seed_catalogue

DRAMA, THRILLER = (9_018, "Drama"), (9_053, "Thriller")
DARK = 9_760_001  # darkness 90, 2010, 95 minutes
LIGHT = 9_760_002  # darkness 20, 1995, 130 minutes
UNSCORED = 9_760_003


def vector(darkness: float, base: float = 60.0) -> list[float]:
    return [darkness if key == "darkness" else base for key in TRAIT_KEYS]


@pytest.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed_catalogue(
        db_session,
        [
            {
                "id": DARK,
                "vector": vector(90.0),
                "runtime": 95,
                "genres": [THRILLER, DRAMA],
                "director": 9_760_901,
                "popularity": 50.0,
            },
            {"id": LIGHT, "vector": vector(20.0), "runtime": 130, "popularity": 40.0},
        ],
    )
    for movie_id, year in ((DARK, 2010), (LIGHT, 1995)):
        movie = await db_session.get(Movie, movie_id)
        assert movie is not None
        movie.release_date = date(year, 6, 1)
    db_session.add(Movie(id=UNSCORED, title="Film unscored", popularity=45.0, adult=False))
    await db_session.commit()
    return db_session


async def _ids(client: httpx.AsyncClient, **params: object) -> list[int]:
    response = await client.get("/movies", params={"q": "Film", "limit": 100, **params})
    assert response.status_code == 200, response.text
    ours = {DARK, LIGHT, UNSCORED}
    return [m["id"] for m in response.json() if m["id"] in ours]


# --- search -------------------------------------------------------------------------


async def test_search_without_filters_is_by_popularity(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        assert await _ids(client) == [DARK, UNSCORED, LIGHT]


async def test_search_by_year_range(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        assert await _ids(client, year_from=2000) == [DARK]
        assert await _ids(client, year_to=1999) == [LIGHT]
        assert await _ids(client, year_from=1990, year_to=2020) == [DARK, LIGHT]


async def test_search_by_runtime(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        assert await _ids(client, max_runtime=95) == [DARK]  # inclusive


async def test_search_by_trait_minimum_leaves_out_unscored_films(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        assert await _ids(client, trait="darkness:70") == [DARK]
        assert await _ids(client, trait="darkness:10") == [DARK, LIGHT]
        both = await client.get(
            "/movies", params=[("q", "Film"), ("trait", "darkness:10"), ("trait", "humor:70")]
        )
    assert [m["id"] for m in both.json() if m["id"] in {DARK, LIGHT}] == []


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"trait": "sparkle:50"}, id="unknown-trait"),
        pytest.param({"trait": "darkness"}, id="no-minimum"),
        pytest.param({"trait": "darkness:high"}, id="minimum-not-a-number"),
        pytest.param({"trait": "darkness:150"}, id="minimum-above-100"),
        pytest.param({"year_from": 1500}, id="year-out-of-range"),
        pytest.param({"max_runtime": 0}, id="runtime-zero"),
        pytest.param({"limit": 0}, id="limit-zero"),
    ],
)
async def test_invalid_search_input_is_422(seeded: AsyncSession, params: dict) -> None:
    async with api_client(seeded) as client:
        response = await client.get("/movies", params=params)
    assert response.status_code == 422


# --- detail -------------------------------------------------------------------------


async def test_detail_signed_out_has_everything_but_the_match(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        response = await client.get(f"/movies/{DARK}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == f"Film {DARK}"
    assert body["runtime_minutes"] == 95
    assert body["genres"] == ["Drama", "Thriller"]
    assert body["director"] == "Director 9760901"
    assert body["traits"]["scores"]["darkness"] == 90.0
    assert set(body["traits"]["scores"]) == set(TRAIT_KEYS)
    assert body["match"] is None
    assert body["reasons"] == []


async def test_detail_of_an_unscored_film_has_no_traits(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        body = (await client.get(f"/movies/{UNSCORED}", headers=auth(uuid.uuid4()))).json()
    assert body["traits"] is None
    assert body["match"] is None


async def test_detail_signed_in_without_a_taste_has_no_match(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        body = (await client.get(f"/movies/{DARK}", headers=auth(uuid.uuid4()))).json()
    assert body["match"] is None


async def test_detail_match_is_recomputable_from_stored_numbers(seeded: AsyncSession) -> None:
    """The film page's match is FR-5 on users.taste_* and movie_traits.vector (CLAUDE.md)."""
    from app.models import User

    me = uuid.uuid4()
    async with api_client(seeded) as client:
        await client.post("/ratings", json={"movie_id": LIGHT, "score": 9}, headers=auth(me))
        body = (await client.get(f"/movies/{DARK}", headers=auth(me))).json()

    user = await seeded.get(User, me, populate_existing=True)
    assert user is not None and user.taste_vector is not None and user.taste_weights
    taste = [float(v) for v in user.taste_vector]
    weights = weights_vector(user.taste_weights)
    expected = match_percentage(taste, weights, vector(90.0))
    assert body["match"] == expected
    rule = await load_rule(seeded)
    assert rule is not None
    assert body["reasons"] == top_reasons(taste, vector(90.0), rule, weights=weights)
    # By hand: taste is LIGHT's vector (one liked film), weights all equal, so the gap is
    # sqrt(70² / 14) = 18.7 points on the one dimension that differs -> 81%.
    assert expected == 81


async def test_detail_not_found_is_404(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        response = await client.get("/movies/999999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Movie not found"}


async def test_detail_invalid_id_is_422(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        assert (await client.get("/movies/0")).status_code == 422
        assert (await client.get("/movies/abc")).status_code == 422


async def test_detail_with_a_forged_token_is_401_not_signed_out(seeded: AsyncSession) -> None:
    forged = auth(uuid.uuid4(), forged=True)
    async with api_client(seeded) as client:
        response = await client.get(f"/movies/{DARK}", headers=forged)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}
