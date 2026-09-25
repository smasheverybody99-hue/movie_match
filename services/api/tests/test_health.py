"""Health endpoints.

`/health` must answer even when no database is configured: it is what the
container orchestrator and the web client's connection check call, and a
health endpoint that needs the database cannot report that the database is
the thing that is down.
"""

from fastapi.testclient import TestClient

from app.traits import TRAIT_COUNT


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_trait_dimensions(client: TestClient) -> None:
    assert client.get("/health").json()["trait_dimensions"] == TRAIT_COUNT


def test_health_works_without_a_database(client: TestClient, monkeypatch) -> None:
    """No DATABASE_URL configured must not turn /health into a 500."""
    monkeypatch.setenv("DATABASE_URL", "")
    assert client.get("/health").status_code == 200


def test_openapi_schema_builds(client: TestClient) -> None:
    """Catches a malformed response model before it reaches a client."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
