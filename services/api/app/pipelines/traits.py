"""Trait extraction: movie -> 14-dimension Movie DNA vector.

Runs as a batch job, never inside a request. Uses Claude Haiku through the Batch API,
which halves the token cost. Budget for ~20k films: roughly $30-60 one-off.
"""

import json
from typing import Any

from app.traits import TRAIT_KEYS

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = f"""You score films on fixed dimensions for a recommendation engine.

Return ONLY a JSON object with exactly these keys, each an integer 0-100:
{", ".join(TRAIT_KEYS)}

Plus one key "summary": two sentences, plain language, describing what kind of viewer
this film is for. No markdown, no commentary outside the JSON.

Scoring guidance:
- 50 means "average for a feature film", not "unknown". Use the full range.
- pacing: 0 contemplative, 100 relentless.
- realism: 0 fully fantastical, 100 grounded.
- darkness: 0 light and warm, 100 bleak.
- ending_ambiguity: 0 fully resolved, 100 deliberately unresolved.
- Score what the film IS, not how good it is. Quality is not a dimension."""


def build_prompt(movie: dict[str, Any]) -> str:
    """One film -> the user message for the batch request."""
    parts = [
        f"Title: {movie['title']}",
        f"Year: {movie.get('year') or 'unknown'}",
        f"Runtime: {movie.get('runtime_minutes') or 'unknown'} minutes",
        f"Genres: {', '.join(movie.get('genres') or []) or 'unknown'}",
        f"Keywords: {', '.join(movie.get('keywords') or []) or 'none'}",
        f"Director: {movie.get('director') or 'unknown'}",
        f"Overview: {movie.get('overview') or 'none'}",
    ]
    return "\n".join(parts)


def parse_response(text: str) -> dict[str, Any]:
    """Model output -> validated scores. Raises on anything malformed."""
    data = json.loads(text)
    scores: dict[str, float] = {}
    for key in TRAIT_KEYS:
        if key not in data:
            raise ValueError(f"missing trait: {key}")
        value = float(data[key])
        if not 0 <= value <= 100:
            raise ValueError(f"{key} out of range: {value}")
        scores[key] = value
    return {"scores": scores, "summary": str(data.get("summary", "")).strip() or None}


# TODO(F1): submit_batch() / collect_batch() using anthropic.beta.messages.batches,
# writing results into MovieTraits. Keep batches at settings.trait_batch_size.
