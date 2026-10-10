"""/health names the deployed commit (docs/deploy.md, 1b) and never fails over it."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.routers import health

SHA = "6e4c40b8f1d2a3c4e5f60718293a4b5c6d7e8f90"


@pytest.fixture(autouse=True)
def fresh_settings() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _commit() -> object:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    return response.json()["commit"]


def test_reports_the_commit_render_deployed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", SHA)
    assert _commit() == SHA


def test_is_null_when_not_on_render(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "")
    assert _commit() is None


@pytest.mark.parametrize("value", ["main", "secret-token-123", SHA + "; rm -rf /", "abc"])
def test_only_ever_echoes_a_hex_sha(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", value)
    assert _commit() is None


def test_answers_even_when_the_settings_cannot_be_read(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> None:
        raise ValueError("bad environment")

    monkeypatch.setattr(health, "get_settings", broken)
    assert _commit() is None
