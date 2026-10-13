"""'Why you'll like this': one or two sentences per (user, film, language), cached forever.

Money rules (CLAUDE.md "Keep the running cost down"):

* The `explanations` table is read before every call; a cached text is never regenerated.
* A user can cause at most `explanation_daily_calls_per_user` generations a day.
* Nothing is generated from nothing: the prompt carries the dimensions that actually
  drive the match (matching.top_reasons). A film with no shared dimension gets no
  explanation rather than a generic compliment.

Generation never blocks or breaks a recommendation: any failure answers with a `Reason`
instead of a sentence, and the client shows the recommendation with its free fallback.
The reason is what lets the interface stop promising a sentence that is not coming.

The configured provider's explainer (`LLM_PROVIDER`, ADR 0006) on its standard (not
batch) API, since a user is waiting. Every generation writes one cost line.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Explanation, Movie, MovieTraits, User
from app.providers import usage as cost_log
from app.providers.base import Explainer
from app.services.matching import top_reasons, weights_vector
from app.services.reasons import load_rule
from app.traits import TRAIT_KEYS, to_dict, trait_labels

log = logging.getLogger(__name__)

__all__ = ["Explained", "Explainer", "Reason", "build_prompt", "cached", "clean", "explain"]

TIMEOUT_SECONDS = 10.0
MAX_CHARS = 400  # longer than two sentences means the model ignored the brief

Lang = Literal["en", "uz", "ru"]  # the same as app.schemas.Lang (a unit test checks)

# Why there is no sentence. Until 2026-10-13 all six answered with the same `text: null`,
# so neither the client nor a log could tell "nothing is configured" from "the model timed
# out" - the interface showed "Writing the explanation..." for up to TIMEOUT_SECONDS and
# then the free fallback, which is what a tester reported (TZ backlog, 2026-10-02).
#
#   no_generator  no provider key, so nothing can be generated at all
#   daily_cap     this user's `explanation_daily_calls_per_user` is used up until tomorrow
#   no_taste      the user has no taste profile yet
#   no_traits     this film has no trait vector, or no film has any (no catalogue stats)
#   no_reasons    no trait stands out, so there is nothing truthful to write about
#   failed        the provider raised or timed out; worth trying again later
#   rejected      the answer came back empty or longer than the brief allows
#
# The same set is mirrored in app.schemas.ExplanationReason (a unit test checks), as Lang is.
Reason = Literal[
    "no_generator", "daily_cap", "no_taste", "no_traits", "no_reasons", "failed", "rejected"
]


@dataclass(frozen=True)
class Explained:
    """A sentence, or why there is none. Exactly one of the two is set."""

    text: str | None = None
    reason: Reason | None = None


LANGUAGE_NAMES = {"en": "English", "uz": "Uzbek (Latin script)", "ru": "Russian"}

# Russian answers translated the English brief word for word ("яркого действия" for action,
# "держит более бодрый темп") and dropped ё, which the interface uses. So a Russian prompt
# names each quality with the interface's own word and asks for natural Russian.
RUSSIAN_STYLE = (
    "Пиши естественным русским языком, используй букву ё, "
    "избегай калек с английского."  # noqa: RUF001 - Cyrillic on purpose
)

SYSTEM_PROMPT = """You write one or two short sentences telling a film fan why a film suits
their taste. Use only the qualities you are given: each is one where this film stands out
from a typical film, in the direction the viewer leans. Say it in plain everyday words and
name what the film does on them, more than most films do. No generic praise ("a must-see",
"you'll love it"), no plot spoilers, no rating numbers, no percentages, no quotation marks,
no markdown."""


def build_prompt(
    movie: Movie,
    reasons: list[str],
    taste: dict[str, float],
    film: dict[str, float],
    lang: Lang,
    typical: dict[str, float],
) -> str:
    """`typical`: the catalogue mean per trait, so the model can say how the film differs."""
    labels = trait_labels("en")
    lines = [
        f"- {labels[key]}: the viewer's taste {round(taste[key])}/100, "
        f"this film {round(film[key])}/100, a typical film {round(typical[key])}/100"
        for key in reasons
    ]
    year = f" ({movie.release_date.year})" if movie.release_date else ""
    prompt = (
        f"Film: {movie.title}{year}\n"
        f"Qualities it takes further than most films, the viewer leaning the same way, "
        f"strongest first:\n" + "\n".join(lines) + "\n\n"
        f"Write the sentences in {LANGUAGE_NAMES[lang]}."
    )
    if lang == "ru":
        names = trait_labels("ru")
        words = "; ".join(f"{labels[key]} = {names[key].lower()}" for key in reasons)
        prompt += f"\nName the qualities with these Russian words: {words}.\n{RUSSIAN_STYLE}"
    return prompt


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
) -> Explained:
    """The cached explanation, else a new one if allowed, else why there is none.

    Never raises: a failed explanation must not fail the request it belongs to.
    """
    now = now or datetime.now(UTC)
    hit = (await cached(session, user_id, [movie_id], lang)).get(movie_id)
    if hit is not None:
        return Explained(text=hit)
    if explainer is None:
        return Explained(reason="no_generator")
    if await generated_today(session, user_id, now) >= daily_cap:
        return Explained(reason="daily_cap")

    user = await session.get(User, user_id)
    row = (
        await session.execute(
            select(Movie, MovieTraits.vector)
            .join(MovieTraits, MovieTraits.movie_id == Movie.id)
            .where(Movie.id == movie_id)
        )
    ).first()
    if user is None or user.taste_vector is None or not user.taste_weights:
        return Explained(reason="no_taste")
    if row is None:
        return Explained(reason="no_traits")
    movie, film_vector = row
    taste = [float(v) for v in user.taste_vector]
    film = [float(v) for v in film_vector]
    weights = weights_vector(user.taste_weights)
    rule = await load_rule(session)
    if rule is None:
        return Explained(reason="no_traits")  # no film has traits, so no catalogue stats
    reasons = top_reasons(taste, film, rule, weights=weights)
    if not reasons:
        return Explained(reason="no_reasons")

    typical = dict(zip(TRAIT_KEYS, rule.stats.mean, strict=True))
    prompt = build_prompt(movie, reasons, to_dict(taste), to_dict(film), lang, typical)
    try:
        generated = await asyncio.wait_for(
            explainer.generate(SYSTEM_PROMPT, prompt), TIMEOUT_SECONDS
        )
    except Exception:  # a failed explanation must never fail the request
        log.warning("explanation failed for movie %s", movie_id, exc_info=True)
        return Explained(reason="failed")
    cost_log.record(
        "explanation", explainer.provider, explainer.model, generated.usage, explainer.pricing
    )
    answer = clean(generated.text)
    if answer is None:
        log.warning("explanation rejected for movie %s: %r", movie_id, generated.text[:120])
        return Explained(reason="rejected")

    await session.execute(
        insert(Explanation)
        .values(user_id=user_id, movie_id=movie_id, lang=lang, text=answer, model=explainer.model)
        .on_conflict_do_nothing(index_elements=["user_id", "movie_id", "lang"])
    )
    await session.commit()
    return Explained(text=answer)
