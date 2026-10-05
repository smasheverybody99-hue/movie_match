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


# Where the match places the film in the catalogue for this user (FR-5, TZ 1.13): one of
# their N closest ("strong"), or in their closest share ("good"). Clients show this, not
# the number; `match` stays for ordering and for checking by hand.
MatchBand = Literal["strong", "good"]
BAND_DESCRIPTION = "The caller's match band (FR-5); null outside both bands, or without a match"


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
    reasons: list[str] = Field(
        default_factory=list, description="Trait keys that drove the match, strongest first"
    )


class RecommendationOut(BaseModel):
    movie: MovieOut
    match: int = Field(ge=0, le=100, description="Match percentage, computed from trait distance")
    band: MatchBand | None = Field(default=None, description=BAND_DESCRIPTION)
    reasons: list[str] = Field(
        default_factory=list, description="Trait keys that drove the match, strongest first"
    )
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


class ExplanationOut(BaseModel):
    movie_id: int
    lang: Lang
    text: str | None = Field(description="Null when it could not be generated; try later")


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
