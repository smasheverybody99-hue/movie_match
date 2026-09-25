"""Pydantic request/response models. Mirrored by hand in apps/web/src/lib/types.ts."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    release_date: date | None = None
    runtime_minutes: int | None = None
    overview: str | None = None
    poster_path: str | None = None


class TraitScores(BaseModel):
    """Trait key -> 0..100. Keys come from packages/shared/traits.json."""

    scores: dict[str, float]
    summary: str | None = None


class MovieDetailOut(MovieOut):
    traits: TraitScores | None = None
    genres: list[str] = Field(default_factory=list)
    director: str | None = None
    cast: list[str] = Field(default_factory=list)


class RecommendationOut(BaseModel):
    movie: MovieOut
    match: int = Field(ge=0, le=100, description="Match percentage, computed from trait distance")
    reasons: list[str] = Field(
        default_factory=list, description="Trait keys that drove the match, strongest first"
    )
    explanation: str | None = None


class RatingIn(BaseModel):
    movie_id: int
    score: float = Field(ge=0.5, le=10.0)
    liked_aspects: list[str] = Field(default_factory=list)


class RatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movie_id: int
    score: float


class MovieDnaOut(BaseModel):
    scores: dict[str, float]
    summary: str | None = None
    rating_count: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str | None = None
    onboarded: bool = False
