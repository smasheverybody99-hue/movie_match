"""Every protected endpoint: 401 without a token, 401 with a forged one, 2xx with a valid one."""

import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from tests.conftest import rolled_back_session
from tests.integration.api import api_client, auth, seed_films, token

# One seeded session for the module (the test database is remote); every test acts as
# its own new user, so tests cannot see each other's rows.
pytestmark = pytest.mark.asyncio(loop_scope="module")

FILM = 9_300_001

# (method, path, json body) for every endpoint that needs a signed-in user.
PROTECTED = [
    ("POST", "/ratings", {"movie_id": FILM, "score": 8}),
    ("GET", "/ratings", None),
    ("DELETE", f"/ratings/{FILM}", None),
    ("GET", "/watchlist", None),
    ("POST", "/watchlist", {"movie_id": FILM}),
    ("DELETE", f"/watchlist/{FILM}", None),
    ("POST", f"/watchlist/{FILM}/watched", None),
    ("GET", "/me", None),
    ("DELETE", "/me", None),
    ("GET", "/recommendations", None),
    ("GET", f"/recommendations/{FILM}/explanation", None),
    ("POST", "/dismissals", {"movie_id": FILM}),
    ("DELETE", f"/dismissals/{FILM}", None),
    ("GET", "/onboarding/films", None),
]
IDS = [f"{m} {p}" for m, p, _ in PROTECTED]


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def seeded(migrated_test_db: None) -> AsyncIterator[AsyncSession]:
    async with rolled_back_session() as session:
        await seed_films(session, {FILM: [60.0] * 14})
        yield session


async def test_every_protected_route_is_listed_here() -> None:
    """Every operation that takes a bearer token must be in PROTECTED, and nothing else.

    Read from the OpenAPI schema: FastAPI 0.141 wraps included routers, so `app.routes`
    no longer lists their paths.
    """
    from app.main import app

    routes = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method, operation in operations.items()
        if operation.get("security")
    }
    listed = {(m, p.replace(str(FILM), "{movie_id}")) for m, p, _ in PROTECTED}
    assert routes == listed


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED, ids=IDS)
async def test_missing_token_is_401(
    seeded: AsyncSession, method: str, path: str, body: dict | None
) -> None:
    async with api_client(seeded) as client:
        response = await client.request(method, path, json=body)
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing bearer token"}


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED, ids=IDS)
async def test_forged_token_is_401(
    seeded: AsyncSession, method: str, path: str, body: dict | None
) -> None:
    forged = auth(uuid.uuid4(), secret="not-the-project-secret-at-all-1234")
    async with api_client(seeded) as client:
        response = await client.request(method, path, json=body, headers=forged)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED, ids=IDS)
async def test_valid_token_is_let_through(
    seeded: AsyncSession, method: str, path: str, body: dict | None
) -> None:
    me = auth(uuid.uuid4())
    async with api_client(seeded) as client:
        # rows for the DELETE and /watched routes to act on
        if method != "GET":
            await client.post("/ratings", json={"movie_id": FILM, "score": 8}, headers=me)
            await client.post("/watchlist", json={"movie_id": FILM}, headers=me)
            await client.post("/dismissals", json={"movie_id": FILM}, headers=me)
        response = await client.request(method, path, json=body, headers=me)
    assert response.status_code in (200, 204), response.text


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param(auth(uuid.uuid4(), expires_in=-60), id="expired"),
        pytest.param(auth(uuid.uuid4(), audience="anon"), id="wrong-audience"),
        pytest.param(auth("not-a-uuid"), id="subject-not-a-uuid"),
        pytest.param({"Authorization": "Bearer not.a.jwt"}, id="garbage"),
        pytest.param({"Authorization": f"Basic {token(uuid.uuid4())}"}, id="not-bearer"),
    ],
)
async def test_bad_tokens_are_401(seeded: AsyncSession, headers: dict[str, str]) -> None:
    async with api_client(seeded) as client:
        response = await client.get("/ratings", headers=headers)
    assert response.status_code == 401


async def test_token_without_subject_is_401(seeded: AsyncSession) -> None:
    import time

    import jwt

    from tests.integration.api import SECRET

    no_sub = jwt.encode(
        {"aud": "authenticated", "exp": int(time.time()) + 60}, SECRET, algorithm="HS256"
    )
    async with api_client(seeded) as client:
        response = await client.get("/ratings", headers={"Authorization": f"Bearer {no_sub}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Token has no subject"}


async def test_missing_server_secret_is_500_not_a_pass(seeded: AsyncSession) -> None:
    async with api_client(seeded, jwt_secret="") as client:
        response = await client.get("/ratings", headers=auth(uuid.uuid4()))
    assert response.status_code == 500


async def test_first_request_creates_the_user_row_once(seeded: AsyncSession) -> None:
    me = uuid.uuid4()
    async with api_client(seeded) as client:
        await client.get("/ratings", headers=auth(me))
        await client.get("/watchlist", headers=auth(me))
    assert await seeded.get(User, me) is not None


async def test_public_routes_need_no_token(seeded: AsyncSession) -> None:
    async with api_client(seeded) as client:
        assert (await client.get("/health")).status_code == 200
