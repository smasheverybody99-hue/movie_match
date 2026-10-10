"""CORS preflight: the browser may cache it for two hours (TZ 1.18)."""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def _preflight(origin: str):
    return TestClient(app).options(
        "/me/dna",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )


def test_preflight_may_be_cached_for_two_hours() -> None:
    origin = get_settings().cors_origin_list[0]
    response = _preflight(origin)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-max-age"] == "7200"


def test_an_unknown_origin_is_still_refused() -> None:
    response = _preflight("https://not-ours.example")
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
