"""TMDB client behaviour under rate limits and failures. No network: a fake transport."""

import time

import httpx
import pytest

from app.pipelines import tmdb
from app.pipelines.tmdb import RateLimiter, TmdbClient, TmdbNotFound


def _client(handler, sleeps: list[float] | None = None) -> TmdbClient:
    async def record_sleep(seconds: float) -> None:
        if sleeps is not None:
            sleeps.append(seconds)

    return TmdbClient(
        "test-key", transport=httpx.MockTransport(handler), rate_per_second=0, sleep=record_sleep
    )


async def test_429_waits_for_retry_after_then_succeeds() -> None:
    responses = iter(
        [
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(200, json={"id": 550, "title": "Fight Club"}),
        ]
    )
    sleeps: list[float] = []
    client = _client(lambda request: next(responses), sleeps)
    assert (await client.movie(550))["title"] == "Fight Club"
    assert sleeps == [3.0]


async def test_429_without_retry_after_backs_off_exponentially() -> None:
    responses = iter([httpx.Response(429)] * 3 + [httpx.Response(200, json={"id": 1})])
    sleeps: list[float] = []
    await _client(lambda request: next(responses), sleeps).movie(1)
    assert sleeps == [1.0, 2.0, 4.0]


async def test_404_is_not_retried() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(404)

    with pytest.raises(TmdbNotFound):
        await _client(handler).movie(999)
    assert calls == ["/3/movie/999"]


async def test_server_errors_give_up_after_max_attempts() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(503)

    with pytest.raises(httpx.HTTPStatusError):
        await _client(handler).movie(1)
    assert len(calls) == tmdb.MAX_ATTEMPTS


async def test_network_errors_are_retried() -> None:
    attempts = iter([httpx.ConnectError("reset"), httpx.Response(200, json={"id": 1})])

    def handler(request: httpx.Request) -> httpx.Response:
        outcome = next(attempts)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    assert (await _client(handler).movie(1))["id"] == 1


async def test_persistent_network_errors_are_raised() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    with pytest.raises(httpx.ConnectError):
        await _client(handler).movie(1)


async def test_movie_request_asks_for_credits_and_keywords() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": 550})

    await _client(handler).movie(550)
    params = seen[0].url.params
    assert params["append_to_response"] == "credits,keywords"
    assert params["api_key"] == "test-key"


async def test_discover_filters_by_decade_votes_and_adult() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "page": 1,
                "total_pages": 7,
                "results": [
                    {
                        "id": 1,
                        "popularity": 9.0,
                        "original_language": "fr",
                        "release_date": "1965-03-01",
                        "vote_count": 300,
                    }
                ],
            },
        )

    candidates, total_pages = await _client(handler).discover(
        page=1, year_from=1960, year_to=1969, min_votes=100
    )
    params = seen[0].url.params
    assert seen[0].url.path == "/3/discover/movie"
    assert params["primary_release_date.gte"] == "1960-01-01"
    assert params["primary_release_date.lte"] == "1969-12-31"
    assert params["vote_count.gte"] == "100"
    assert params["include_adult"] == "false"
    assert params["sort_by"] == "popularity.desc"
    assert total_pages == 7
    assert candidates[0].language == "fr" and candidates[0].year == 1965


def test_missing_api_key_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "tmdb_api_key", "")
    with pytest.raises(RuntimeError, match="TMDB_API_KEY"):
        TmdbClient()


async def test_rate_limiter_spaces_requests() -> None:
    limiter = RateLimiter(rate_per_second=50)  # 20 ms apart
    start = time.monotonic()
    for _ in range(4):
        await limiter.acquire()
    assert time.monotonic() - start >= 0.055  # three gaps of 20 ms, with timer slack


async def test_context_manager_closes_the_http_client() -> None:
    client = _client(lambda request: httpx.Response(200, json={}))
    async with client:
        pass
    assert client._client.is_closed
