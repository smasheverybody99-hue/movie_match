"""Pydantic request/response models. Mirrored by hand in apps/web/src/lib/types.ts."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.traits import TRAIT_KEYS


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    release_date: date | None = None
    runtime_minutes: int | None = None
    overview: str | None = None
    poster_path: str | None = None
    # Every film carries it (not only the detail): the Home hero shows the top picks'
    # backdrops from the recommendations response (docs/ui.md, 4a).
    backdrop_path: str | None = None
    # Alphabetical. Lists carry them too: a poster that cannot load shows the title, the
    # year and the genre instead (tester 1, 2026-10-12).
    genres: list[str] = Field(default_factory=list)


# Where the match places the film in the catalogue for this user (FR-5, TZ 1.13): one of
# their N closest ("strong"), or in their closest share ("good"). Clients show this, not
# the number; `match` stays for ordering and for checking by hand.
MatchBand = Literal["strong", "good"]
BAND_DESCRIPTION = "The caller's match band (FR-5); null outside both bands, or without a match"

# The traits the panel names, and which side they fall on (FR-5, TZ 1.23): the same set as
# app.services.matching.TraitSide (a unit test checks). "reason" - the film goes further
# the way the caller leans; "difference" - it goes the other way, far enough to say so.
# Reasons win: a film with any reason never reports differences. Both null and empty means
# nothing is worth saying, and the client writes no sentence at all.
TraitSide = Literal["reason", "difference"]
NAMED_TRAITS_DESCRIPTION = "Trait keys worth naming, strongest first; empty when none is"
TRAIT_SIDE_DESCRIPTION = (
    "Which side `named_traits` falls on; null exactly when `named_traits` is empty"
)


class TraitScores(BaseModel):
    """Trait key -> 0..100. Keys come from packages/shared/traits.json."""

    scores: dict[str, float]
    summary: str | None = None


class MovieDetailOut(MovieOut):
    traits: TraitScores | None = None
    genres: list[str] = Field(default_factory=list)
    director: str | None = None
    cast: list[str] = Field(default_factory=list)
    match: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="The caller's match (FR-5). Null signed out, or without traits or taste",
    )
    band: MatchBand | None = Field(default=None, description=BAND_DESCRIPTION)
    named_traits: list[str] = Field(default_factory=list, description=NAMED_TRAITS_DESCRIPTION)
    trait_side: TraitSide | None = Field(default=None, description=TRAIT_SIDE_DESCRIPTION)


class RecommendationOut(BaseModel):
    movie: MovieOut
    match: int = Field(ge=0, le=100, description="Match percentage, computed from trait distance")
    band: MatchBand | None = Field(default=None, description=BAND_DESCRIPTION)
    named_traits: list[str] = Field(default_factory=list, description=NAMED_TRAITS_DESCRIPTION)
    trait_side: TraitSide | None = Field(default=None, description=TRAIT_SIDE_DESCRIPTION)
    explanation: str | None = None


# English is the default and the source language; Uzbek second, Russian added (TZ 1.8).
Lang = Literal["en", "uz", "ru"]
SectionKey = Literal["for_you", "because_you_loved", "under_90", "outside_usual"]


class SectionOut(BaseModel):
    """One row of recommendations. Clients turn `key` into a title in the user's language."""

    key: SectionKey
    seed: MovieOut | None = Field(
        default=None, description="The film in 'Because you loved {film}'; null otherwise"
    )
    items: list[RecommendationOut]


class RecommendationsOut(BaseModel):
    status: Literal["ok", "not_enough_data"]
    ratings_needed: int = Field(ge=0, description="Ratings still needed before recommendations")
    sections: list[SectionOut] = Field(default_factory=list)


# The same set as app.services.explain.Reason (a unit test checks), so the client can tell
# "nothing is configured" from "the model timed out" and stop promising a sentence that is
# not coming.
ExplanationReason = Literal[
    "no_generator", "daily_cap", "no_taste", "no_traits", "no_reasons", "failed", "rejected"
]


class ExplanationOut(BaseModel):
    movie_id: int
    lang: Lang
    text: str | None = Field(description="Null when there is none to give; see `reason`")
    reason: ExplanationReason | None = Field(
        default=None, description="Why `text` is null; null when there is a text"
    )


class DismissalIn(BaseModel):
    movie_id: int = Field(gt=0)


class MeOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    rating_count: int
    ratings_needed: int = Field(ge=0, description="Ratings still needed before recommendations")
    has_taste_profile: bool
    taste_updated_at: datetime | None = None


class RatingIn(BaseModel):
    movie_id: int = Field(gt=0)
    score: float = Field(ge=0.5, le=10.0)
    liked_aspects: list[str] = Field(
        default_factory=list, max_length=len(TRAIT_KEYS), description="Trait keys, no repeats"
    )

    @field_validator("liked_aspects")
    @classmethod
    def _known_trait_keys(cls, value: list[str]) -> list[str]:
        unknown = [key for key in value if key not in TRAIT_KEYS]
        if unknown:
            raise ValueError(f"unknown trait keys: {', '.join(unknown)}")
        if len(set(value)) != len(value):
            raise ValueError("repeated trait key")
        return value


class RatingOut(BaseModel):
    movie_id: int
    score: float
    liked_aspects: list[str] = Field(default_factory=list)
    rated_at: datetime = Field(description="When the score was last set")


class WatchlistIn(BaseModel):
    movie_id: int = Field(gt=0)


class WatchlistItemOut(BaseModel):
    movie: MovieOut
    added_at: datetime
    watched_at: datetime | None = None
    match: int | None = Field(
        default=None, ge=0, le=100, description="The caller's match; null without traits or taste"
    )
    band: MatchBand | None = Field(default=None, description=BAND_DESCRIPTION)


class MovieDnaOut(BaseModel):
    scores: dict[str, float] = Field(
        description="The taste vector by trait key, 0..100. Empty until a scored film is liked"
    )
    summary: str | None = Field(
        default=None, description="AI summary. Not generated yet (backlog): always null"
    )
    rating_count: int
    ratings_needed: int = Field(ge=0, description="Ratings still needed before the DNA shows")
    average_rating: float | None = None
    top_genre: str | None = Field(
        default=None, description="The genre on most of the user's rated films"
    )


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str | None = None
    onboarded: bool = False
