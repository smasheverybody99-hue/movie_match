"""The one place a Gemini client is built. Pipelines take the client as an argument."""

from typing import Any

from google import genai

from app.config import Settings


def gemini_client(settings: Settings) -> Any:
    """Async Gemini client (`client.batches`, `client.models`) or exit with a clear message."""
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY is not configured")
    return genai.Client(api_key=settings.gemini_api_key).aio
