"""'Why you'll like this': one or two sentences per (user, film, language), cached forever.

Money rules (CLAUDE.md "Keep the running cost down"):

* The `explanations` table is read before every call; a cached text is never regenerated.
* A user can cause at most `explanation_daily_calls_per_user` generations a day.
* Nothing is generated from nothing: the prompt carries the dimensions the one rule found
  worth naming (matching.trait_notes), and the brief follows the side it found - why the
  film suits them, or how it differs from them. A film with nothing worth naming gets no
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
from app.services.matching import TraitNotes, TraitSide, trait_notes, weights_vector
from app.services.reasons import load_rule
from app.traits import TRAIT_KEYS, to_dict, trait_labels

log = logging.getLogger(__name__)

__all__ = [
    "Explained",
    "Explainer",
    "Reason",
    "build_prompt",
    "cached",
    "clean",
    "explain",
    "system_prompt",
]

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
#   nothing_named the rule found no trait worth naming on either side (TZ 1.23), so there
#                 is nothing truthful to write - neither why it suits them nor how it
#                 differs. Named for what it means: a name mentioning only reasons would
#                 suggest a difference might still be coming.
#   failed        the provider raised or timed out; worth trying again later
#   rejected      the answer came back empty or longer than the brief allows
#
# The same set is mirrored in app.schemas.ExplanationReason (a unit test checks), as Lang is.
Reason = Literal[
    "no_generator", "daily_cap", "no_taste", "no_traits", "nothing_named", "failed", "rejected"
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
their taste. Use only the qualities you are given: each is one where this film goes further
than a typical film in the direction the viewer leans. Say it in plain everyday words and
name what the film does on them, more than most films do. No generic praise ("a must-see",
"you'll love it"), no plot spoilers, no rating numbers, no percentages, no quotation marks,
no markdown."""

# A film with no reason of its own is described by how it differs, and nothing in that
# sentence may suggest the viewer will like it: that pairing - "outside your taste" over a
# "you'll like this" sentence - is the contradiction a user reported on 2026-10-15.
DIFFERENCE_SYSTEM_PROMPT = """You write one or two short sentences telling a film fan how a
film differs from what they usually go for. Use only the qualities you are given: on each,
this film sits well away from their taste, in the direction away from it.

Every sentence is a comparison and must carry both of its halves: what this viewer usually
goes for on that quality, and where this film sits against it. Name the viewer's side in
words ("you usually go for", "the films you rate highest") and then the film's side, so the
difference is stated rather than left to be inferred: "you usually go for twisty plots;
this one tells its story straight", "there is far less humour here than in the films you
pick". A sentence that only describes the film has not done the job.

State it plainly, as information, and name which way each quality goes. Use no word that
judges the difference ("surprisingly", "refreshingly", "oddly", "sadly", "unfortunately"):
a difference is neither good nor bad. Do not say or imply that they will like it, dislike
it, or should watch it; do not recommend it, warn them off it, or call it a change of pace,
a surprise or worth trying. No plot spoilers, no rating numbers, no percentages, no
quotation marks, no markdown."""


def system_prompt(side: TraitSide) -> str:
    """The brief for this film's side. One rule decided the side; the brief follows it."""
    return SYSTEM_PROMPT if side == "reason" else DIFFERENCE_SYSTEM_PROMPT


def build_prompt(
    movie: Movie,
    notes: TraitNotes,
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
        for key in notes.keys
    ]
    heading = (
        "Qualities it takes further than most films, the viewer leaning the same way"
        if notes.side == "reason"
        else "Qualities on which it sits well away from this viewer's taste, away from it"
    )
    year = f" ({movie.release_date.year})" if movie.release_date else ""
    prompt = (
        f"Film: {movie.title}{year}\n"
        f"{heading}, strongest first:\n" + "\n".join(lines) + "\n\n"
        f"Write the sentences in {LANGUAGE_NAMES[lang]}."
    )
    if lang == "ru":
        names = trait_labels("ru")
        words = "; ".join(f"{labels[key]} = {names[key].lower()}" for key in notes.keys)
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
    notes = trait_notes(taste, film, rule, weights=weights)
    if notes.side is None:
        return Explained(reason="nothing_named")

    typical = dict(zip(TRAIT_KEYS, rule.stats.mean, strict=True))
    prompt = build_prompt(movie, notes, to_dict(taste), to_dict(film), lang, typical)
    try:
        generated = await asyncio.wait_for(
            explainer.generate(system_prompt(notes.side), prompt), TIMEOUT_SECONDS
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
