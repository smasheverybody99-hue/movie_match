"""Helpers for API tests: the app on the rolled-back test session, and signed tokens.

The app runs in-process through httpx's ASGI transport, on the test's own event loop and
database session, so everything a request writes disappears with the test.
"""

import time
import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import httpx
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_session
from app.deps import get_explainer
from app.main import app
from app.models import EMBEDDING_DIM, MovieEmbedding, MovieTraits
from app.pipelines.ingest import SqlIngestStore
from app.pipelines.tmdb import to_film_record
from app.traits import TRAIT_COUNT, TRAIT_KEYS

SECRET = "test-jwt-secret-for-the-api-tests-only"


def token(
    user_id: uuid.UUID | str,
    *,
    secret: str = SECRET,
    audience: str = "authenticated",
    expires_in: int = 3600,
) -> str:
    """A Supabase-shaped access token."""
    now = int(time.time())
    claims = {"sub": str(user_id), "aud": audience, "iat": now, "exp": now + expires_in}
    return jwt.encode(claims, secret, algorithm="HS256")


def auth(user_id: uuid.UUID | str, **kwargs: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(user_id, **kwargs)}"}  # type: ignore[arg-type]


@asynccontextmanager
async def api_client(
    session: AsyncSession,
    *,
    jwt_secret: str = SECRET,
    explainer: object = None,
    settings: dict | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    """The app on `session`. No explanation generator unless a fake one is passed:
    tests never reach a real LLM."""

    async def _session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, supabase_jwt_secret=jwt_secret, **(settings or {})
    )
    app.dependency_overrides[get_explainer] = lambda: explainer
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()


async def seed_films(session: AsyncSession, vectors: dict[int, Sequence[float] | None]) -> None:
    """Films with hand-written trait vectors. None: the film exists but is not scored yet."""
    store = SqlIngestStore(session)
    for movie_id, vector in vectors.items():
        await store.upsert_film(
            to_film_record({"id": movie_id, "title": f"Film {movie_id}", "popularity": 1.0})
        )
        if vector is not None:
            assert len(vector) == TRAIT_COUNT
            scores = dict(zip(TRAIT_KEYS, (float(v) for v in vector), strict=True))
            session.add(
                MovieTraits(
                    movie_id=movie_id,
                    scores=scores,
                    vector=list(scores.values()),
                    model="hand-written",
                    spec_version=1,
                )
            )
    await session.commit()


def fake_embedding(vector: Sequence[float]) -> list[float]:
    """A 1,536-d embedding that points where the trait vector does.

    Traits centred on 50, so opposite films point opposite ways, then padded; the
    constant keeps a film of all-50 traits from being a zero vector.
    """
    head = [float(v) - 50.0 for v in vector] + [1.0]
    return head + [0.0] * (EMBEDDING_DIM - len(head))


async def seed_catalogue(session: AsyncSession, films: Sequence[dict]) -> None:
    """Films with traits, an embedding, and optionally a director, runtime and genres.

    Each dict: id, vector, and any of director (person id), runtime, popularity,
    genres ([(id, name)]), embedding (defaults to fake_embedding(vector)).
    """
    records = []
    for film in films:
        crew = []
        if film.get("director") is not None:
            crew.append(
                {
                    "id": film["director"],
                    "name": f"Director {film['director']}",
                    "job": "Director",
                    "department": "Directing",
                }
            )
        payload = {
            "id": film["id"],
            "title": f"Film {film['id']}",
            "popularity": film.get("popularity", 1.0),
            "runtime": film.get("runtime", 120),
            "genres": [{"id": g, "name": n} for g, n in film.get("genres", [])],
            "credits": {"cast": [], "crew": crew},
        }
        records.append(to_film_record(payload))
    # One statement per table: the test database is a network round trip away.
    await SqlIngestStore(session).upsert_films(records)
    for film in films:
        vector = [float(v) for v in film["vector"]]
        scores = dict(zip(TRAIT_KEYS, vector, strict=True))
        session.add(
            MovieTraits(
                movie_id=film["id"],
                scores=scores,
                vector=vector,
                model="hand-written",
                spec_version=1,
            )
        )
        session.add(
            MovieEmbedding(
                movie_id=film["id"],
                embedding=film.get("embedding") or fake_embedding(vector),
                model="hand-written",
            )
        )
    await session.commit()
