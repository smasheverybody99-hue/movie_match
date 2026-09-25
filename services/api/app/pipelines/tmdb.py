"""TMDB client — the only module that knows TMDB's field names.

Everything downstream works with our own shapes (`Candidate`, `FilmRecord`), so the data
source can be replaced without touching the rest of the codebase. See docs/legal.md and
ADR 0002: free tier for development, commercial licence before monetization.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx

from app.config import get_settings

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p"

MAX_ATTEMPTS = 5
CAST_LIMIT = 15
CREW_JOBS = {"Director", "Screenplay", "Writer"}


class TmdbNotFound(Exception):
    """TMDB answered 404: the film was removed or merged. Skip it, don't retry."""


@dataclass(frozen=True)
class Candidate:
    """A film offered by discovery, before we decide whether to ingest it."""

    id: int
    popularity: float
    language: str
    year: int | None
    vote_count: int


@dataclass
class FilmRecord:
    """One film in our shape, ready to upsert."""

    movie: dict[str, Any]
    genres: list[tuple[int, str]] = field(default_factory=list)
    keywords: list[tuple[int, str]] = field(default_factory=list)
    people: list[dict[str, Any]] = field(default_factory=list)
    credits: list[dict[str, Any]] = field(default_factory=list)


class RateLimiter:
    """Spaces requests at least 1/rate seconds apart, across concurrent callers."""

    def __init__(self, rate_per_second: float) -> None:
        self._interval = 1.0 / rate_per_second if rate_per_second > 0 else 0.0
        self._next = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._next - now
            self._next = max(now, self._next) + self._interval
        if wait > 0:
            await asyncio.sleep(wait)


class TmdbClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        rate_per_second: float | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.tmdb_api_key
        if not self._api_key:
            raise RuntimeError("TMDB_API_KEY is not configured")
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=20.0, transport=transport)
        self._limiter = RateLimiter(
            settings.tmdb_requests_per_second if rate_per_second is None else rate_per_second
        )
        self._sleep = sleep

    async def __aenter__(self) -> "TmdbClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **params: Any) -> dict:
        """GET with backoff. Retries 429 (honouring Retry-After), 5xx and network errors."""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            await self._limiter.acquire()
            try:
                response = await self._client.get(path, params={"api_key": self._api_key, **params})
            except httpx.TransportError:
                if attempt == MAX_ATTEMPTS:
                    raise
                await self._sleep(_backoff(attempt))
                continue

            if response.status_code == 404:
                raise TmdbNotFound(path)
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == MAX_ATTEMPTS:
                    response.raise_for_status()
                await self._sleep(_retry_after(response) or _backoff(attempt))
                continue
            response.raise_for_status()
            return response.json()
        raise AssertionError("unreachable")  # pragma: no cover

    async def movie(self, movie_id: int) -> dict:
        """Full movie record with credits and keywords in one request."""
        return await self._get(f"/movie/{movie_id}", append_to_response="credits,keywords")

    async def discover(
        self, *, page: int, year_from: int, year_to: int, min_votes: int
    ) -> tuple[list[Candidate], int]:
        """One page of films released in [year_from, year_to], most popular first.

        Returns the candidates and the total page count.
        """
        payload = await self._get(
            "/discover/movie",
            page=page,
            sort_by="popularity.desc",
            include_adult="false",
            include_video="false",
            **{
                "primary_release_date.gte": f"{year_from}-01-01",
                "primary_release_date.lte": f"{year_to}-12-31",
                "vote_count.gte": min_votes,
            },
        )
        candidates = [to_candidate(r) for r in payload.get("results", [])]
        return candidates, int(payload.get("total_pages") or 0)


def _backoff(attempt: int) -> float:
    return float(min(2 ** (attempt - 1), 20))


def _retry_after(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def _clip(value: Any, limit: int) -> str | None:
    """Fit free text into its column. TMDB has character names over 300 characters."""
    if value is None or value == "":
        return None
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def to_candidate(result: dict) -> Candidate:
    released = _parse_date(result.get("release_date"))
    return Candidate(
        id=int(result["id"]),
        popularity=float(result.get("popularity") or 0.0),
        language=str(result.get("original_language") or "xx"),
        year=released.year if released else None,
        vote_count=int(result.get("vote_count") or 0),
    )


def to_movie_fields(payload: dict) -> dict:
    """TMDB payload -> our Movie column names. The translation boundary."""
    return {
        "id": payload["id"],
        "title": _clip(payload.get("title") or payload.get("original_title"), 500) or "",
        "original_title": _clip(payload.get("original_title"), 500),
        "overview": payload.get("overview") or None,
        "release_date": _parse_date(payload.get("release_date")),
        "runtime_minutes": payload.get("runtime") or None,
        "original_language": _clip(payload.get("original_language"), 10),
        "poster_path": _clip(payload.get("poster_path"), 255),
        "backdrop_path": _clip(payload.get("backdrop_path"), 255),
        "tmdb_vote_average": payload.get("vote_average"),
        "tmdb_vote_count": payload.get("vote_count"),
        "popularity": payload.get("popularity"),
        "adult": bool(payload.get("adult", False)),
    }


def to_film_record(payload: dict) -> FilmRecord:
    """A full /movie/{id} payload (with credits and keywords appended) -> FilmRecord."""
    movie_id = int(payload["id"])
    genres = [(int(g["id"]), _clip(g["name"], 100) or "") for g in payload.get("genres") or []]
    keywords = [
        (int(k["id"]), _clip(k["name"], 200) or "")
        for k in (payload.get("keywords") or {}).get("keywords") or []
    ]

    people: dict[int, dict[str, Any]] = {}
    credits: list[dict[str, Any]] = []
    credit_block = payload.get("credits") or {}

    cast = sorted(credit_block.get("cast") or [], key=lambda c: c.get("order", 999))
    for member in cast[:CAST_LIMIT]:
        person_id = int(member["id"])
        people[person_id] = _person(member)
        credits.append(
            {
                "movie_id": movie_id,
                "person_id": person_id,
                "department": "cast",
                "job": None,
                "character_name": _clip(member.get("character"), 300),
                "billing_order": member.get("order"),
            }
        )

    for member in credit_block.get("crew") or []:
        if member.get("job") not in CREW_JOBS:
            continue
        person_id = int(member["id"])
        people[person_id] = _person(member)
        credits.append(
            {
                "movie_id": movie_id,
                "person_id": person_id,
                "department": _clip(str(member.get("department") or "").lower(), 50) or "crew",
                "job": _clip(member.get("job"), 100),
                "character_name": None,
                "billing_order": None,
            }
        )

    return FilmRecord(
        movie=to_movie_fields(payload),
        genres=genres,
        keywords=keywords,
        people=list(people.values()),
        credits=credits,
    )


def _person(member: dict) -> dict[str, Any]:
    return {
        "id": int(member["id"]),
        "name": _clip(member.get("name"), 300) or "",
        "profile_path": _clip(member.get("profile_path"), 255),
    }
