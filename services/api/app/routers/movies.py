"""Movie search and detail. HTTP only: the logic is in app/services/movies.py."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import optional_user_id
from app.schemas import MovieDetailOut, MovieOut, TraitScores
from app.services import movies

router = APIRouter(prefix="/movies", tags=["movies"])


def _trait_filters(values: list[str]) -> tuple[movies.TraitFilter, ...]:
    """`key:minimum` strings -> filters; anything malformed is a 422."""
    filters = []
    for value in values:
        key, sep, minimum = value.partition(":")
        try:
            if not sep:
                raise ValueError("expected key:minimum")
            filters.append(movies.TraitFilter(key=key, minimum=float(minimum)))
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"Invalid trait filter '{value}': {exc}"
            ) from exc
    return tuple(filters)


@router.get("", response_model=list[MovieOut])
async def search_movies(
    q: str = Query("", max_length=200, description="Title substring"),
    year_from: int | None = Query(None, ge=1870, le=2100),
    year_to: int | None = Query(None, ge=1870, le=2100),
    max_runtime: int | None = Query(None, ge=1, le=1000, description="Minutes, inclusive"),
    trait: list[str] = Query(
        [], max_length=14, description="Repeatable `key:minimum`, e.g. `darkness:70`"
    ),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[MovieOut]:
    filters = movies.SearchFilters(
        q=q,
        year_from=year_from,
        year_to=year_to,
        max_runtime=max_runtime,
        traits=_trait_filters(trait),
    )
    return [MovieOut.model_validate(m) for m in await movies.search(session, filters, limit)]


@router.get("/{movie_id}", response_model=MovieDetailOut)
async def get_movie(
    movie_id: int = Path(gt=0),
    user_id: uuid.UUID | None = Depends(optional_user_id),
    session: AsyncSession = Depends(get_session),
) -> MovieDetailOut:
    """The film. With a token, also the caller's match and its reasons."""
    detail = await movies.get_detail(session, movie_id)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found")
    personal = (
        (await movies.personal_matches(session, user_id, [movie_id])).get(movie_id)
        if user_id is not None
        else None
    )
    base = MovieOut.model_validate(detail.movie)
    return MovieDetailOut(
        **base.model_dump(),
        backdrop_path=detail.movie.backdrop_path,
        traits=(
            TraitScores(scores=detail.scores, summary=detail.summary)
            if detail.scores is not None
            else None
        ),
        genres=detail.genres,
        director=detail.director,
        cast=detail.cast,
        match=personal.match if personal else None,
        reasons=personal.reasons if personal else [],
    )
