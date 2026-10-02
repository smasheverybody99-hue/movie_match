"""'Why you'll like this': one or two sentences per (user, film, language), cached forever.

Money rules (CLAUDE.md "Keep the running cost down"):

* The `explanations` table is read before every call; a cached text is never regenerated.
* A user can cause at most `explanation_daily_calls_per_user` generations a day.
* Nothing is generated from nothing: the prompt carries the dimensions that actually
  drive the match (matching.top_reasons). A film with no shared dimension gets no
  explanation rather than a generic compliment.

Generation never blocks or breaks a recommendation: any failure returns None, and the
client shows the recommendation without the sentence.

The configured provider's explainer (`LLM_PROVIDER`, ADR 0006) on its standard (not
batch) API, since a user is waiting. Every generation writes one cost line.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Explanation, Movie, MovieTraits, User
from app.providers import usage as cost_log
from app.providers.base import Explainer
from app.services.matching import top_reasons, weights_vector
from app.traits import to_dict, trait_labels

log = logging.getLogger(__name__)

__all__ = ["Explainer", "build_prompt", "cached", "clean", "explain"]

TIMEOUT_SECONDS = 10.0
MAX_CHARS = 400  # longer than two sentences means the model ignored the brief

Lang = Literal["en", "uz", "ru"]  # the same as app.schemas.Lang (a unit test checks)
LANGUAGE_NAMES = {"en": "English", "uz": "Uzbek (Latin script)", "ru": "Russian"}

SYSTEM_PROMPT = """You write one or two short sentences telling a film fan why a film suits
their taste. Use only the shared qualities you are given, in plain everyday words, and
name what the film does on them. No generic praise ("a must-see", "you'll love it"), no
plot spoilers, no rating numbers, no percentages, no quotation marks, no markdown."""


def build_prompt(
    movie: Movie,
    reasons: list[str],
    taste: dict[str, float],
    film: dict[str, float],
    lang: Lang,
) -> str:
    labels = trait_labels("en")
    lines = [
        f"- {labels[key]}: the viewer's taste {round(taste[key])}/100, "
        f"this film {round(film[key])}/100"
        for key in reasons
    ]
    year = f" ({movie.release_date.year})" if movie.release_date else ""
    return (
        f"Film: {movie.title}{year}\n"
        f"Shared qualities, strongest first:\n" + "\n".join(lines) + "\n\n"
        f"Write the sentences in {LANGUAGE_NAMES[lang]}."
    )


def clean(raw: str) -> str | None:
    """One line, trimmed; None if empty or too long to be what was asked for."""
    line = " ".join(raw.split()).strip().strip('"')
    if not line or len(line) > MAX_CHARS:
        return None
    return line


async def cached(
    session: AsyncSession, user_id: uuid.UUID, movie_ids: list[int], lang: Lang
) -> dict[int, str]:
    if not movie_ids:
        return {}
    rows = await session.execute(
        select(Explanation.movie_id, Explanation.text).where(
            Explanation.user_id == user_id,
            Explanation.lang == lang,
            Explanation.movie_id.in_(movie_ids),
        )
    )
    return {movie_id: text for movie_id, text in rows.all()}


async def generated_today(session: AsyncSession, user_id: uuid.UUID, now: datetime) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(Explanation)
        .where(Explanation.user_id == user_id, Explanation.created_at > now - timedelta(days=1))
    )
    return count or 0


async def explain(
    session: AsyncSession,
    user_id: uuid.UUID,
    movie_id: int,
    lang: Lang,
    explainer: Explainer | None,
    daily_cap: int,
    now: datetime | None = None,
) -> str | None:
    """The cached explanation, else a new one if allowed, else None. Never raises."""
    now = now or datetime.now(UTC)
    hit = (await cached(session, user_id, [movie_id], lang)).get(movie_id)
    if hit is not None:
        return hit
    if explainer is None or await generated_today(session, user_id, now) >= daily_cap:
        return None

    user = await session.get(User, user_id)
    row = (
        await session.execute(
            select(Movie, MovieTraits.vector)
            .join(MovieTraits, MovieTraits.movie_id == Movie.id)
            .where(Movie.id == movie_id)
        )
    ).first()
    if user is None or user.taste_vector is None or not user.taste_weights or row is None:
        return None
    movie, film_vector = row
    taste = [float(v) for v in user.taste_vector]
    film = [float(v) for v in film_vector]
    weights = weights_vector(user.taste_weights)
    reasons = top_reasons(taste, film, weights=weights)
    if not reasons:
        return None

    prompt = build_prompt(movie, reasons, to_dict(taste), to_dict(film), lang)
    try:
        generated = await asyncio.wait_for(
            explainer.generate(SYSTEM_PROMPT, prompt), TIMEOUT_SECONDS
        )
    except Exception:  # a failed explanation must never fail the request
        log.warning("explanation failed for movie %s", movie_id, exc_info=True)
        return None
    cost_log.record(
        "explanation", explainer.provider, explainer.model, generated.usage, explainer.pricing
    )
    answer = clean(generated.text)
    if answer is None:
        return None

    await session.execute(
        insert(Explanation)
        .values(user_id=user_id, movie_id=movie_id, lang=lang, text=answer, model=explainer.model)
        .on_conflict_do_nothing(index_elements=["user_id", "movie_id", "lang"])
    )
    await session.commit()
    return answer
