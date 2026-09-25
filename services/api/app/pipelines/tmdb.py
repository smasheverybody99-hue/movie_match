"""TMDB client — the only module that knows TMDB's field names.

Everything downstream works with our own model shapes, so the data source can be
replaced without touching the rest of the codebase. See docs/legal.md: a commercial
licence is required before public launch.
"""

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p"


class TmdbClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or get_settings().tmdb_api_key
        if not self._api_key:
            raise RuntimeError("TMDB_API_KEY is not configured")
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=20.0)

    async def __aenter__(self) -> "TmdbClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=20))
    async def _get(self, path: str, **params: Any) -> dict:
        response = await self._client.get(path, params={"api_key": self._api_key, **params})
        response.raise_for_status()
        return response.json()

    async def movie(self, movie_id: int) -> dict:
        """Full movie record with credits and keywords in one request."""
        return await self._get(
            f"/movie/{movie_id}", append_to_response="credits,keywords,watch/providers"
        )

    async def popular(self, page: int = 1) -> dict:
        return await self._get("/movie/popular", page=page)


def to_movie_fields(payload: dict) -> dict:
    """TMDB payload -> our Movie column names. The translation boundary."""
    return {
        "id": payload["id"],
        "title": payload.get("title") or payload.get("original_title") or "",
        "original_title": payload.get("original_title"),
        "overview": payload.get("overview") or None,
        "release_date": payload.get("release_date") or None,
        "runtime_minutes": payload.get("runtime"),
        "original_language": payload.get("original_language"),
        "poster_path": payload.get("poster_path"),
        "backdrop_path": payload.get("backdrop_path"),
        "tmdb_vote_average": payload.get("vote_average"),
        "tmdb_vote_count": payload.get("vote_count"),
        "popularity": payload.get("popularity"),
        "adult": bool(payload.get("adult", False)),
    }
