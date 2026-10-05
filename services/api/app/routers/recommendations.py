"""Recommendations, their explanations, and dismissing a film.

HTTP only: the logic is in app/services/recommend.py and app/services/explain.py.
GET /recommendations never calls an LLM: it attaches explanations that are already
cached, and the client asks for a missing one per film (FR-6: the screen never waits).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_session
from app.deps import current_user, get_explainer
from app.schemas import (
    DismissalIn,
    ExplanationOut,
    Lang,
    MovieOut,
    RecommendationOut,
    RecommendationsOut,
    SectionOut,
)
from app.services import dismissals, explain, recommend
from app.services.explain import Explainer
from app.services.ratings import MovieNotFound

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations", response_model=RecommendationsOut)
async def get_recommendations(
    lang: Lang = Query("en"),
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> RecommendationsOut:
    """Sections of recommendations, or `not_enough_data` below 10 ratings."""
    result = await recommend.recommend(session, user_id)
    if result.ratings_needed:
        return RecommendationsOut(status="not_enough_data", ratings_needed=result.ratings_needed)
    ids = [item.movie_id for section in result.sections for item in section.items]
    texts = await explain.cached(session, user_id, ids, lang)
    return RecommendationsOut(
        status="ok",
        ratings_needed=0,
        sections=[
            SectionOut(
                key=section.key,
                seed=MovieOut.model_validate(section.seed) if section.seed else None,
                items=[
                    RecommendationOut(
                        movie=MovieOut.model_validate(item.candidate.movie),
                        match=item.match,
                        band=item.band,
                        reasons=item.reasons,
                        explanation=texts.get(item.movie_id),
                    )
                    for item in section.items
                ],
            )
            for section in result.sections
        ],
    )


@router.get("/recommendations/{movie_id}/explanation", response_model=ExplanationOut)
async def get_explanation(
    movie_id: int = Path(gt=0),
    lang: Lang = Query("en"),
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
    explainer: Explainer | None = Depends(get_explainer),
    settings: Settings = Depends(get_settings),
) -> ExplanationOut:
    """The cached sentence, or a new one. `text` is null when there is none to give."""
    if not await recommend.movie_exists(session, movie_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found")
    text = await explain.explain(
        session,
        user_id,
        movie_id,
        lang,
        explainer,
        daily_cap=settings.explanation_daily_calls_per_user,
    )
    return ExplanationOut(movie_id=movie_id, lang=lang, text=text)


@router.post("/dismissals", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss(
    body: DismissalIn,
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """'Not for me': the film is never recommended to the caller again."""
    try:
        await dismissals.dismiss(session, user_id, body.movie_id)
    except MovieNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/dismissals/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def undismiss(
    movie_id: int = Path(gt=0),
    user_id: uuid.UUID = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        await dismissals.undismiss(session, user_id, movie_id)
    except dismissals.NotDismissed as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not dismissed") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
