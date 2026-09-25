"""Movie search and detail.

Placeholder implementations for F0: the routes and contracts exist so the web and
mobile clients can be built against them. Real queries land in F1/F2.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Movie
from app.schemas import MovieDetailOut, MovieOut

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=list[MovieOut])
async def search_movies(
    q: str = Query("", max_length=200, description="Title substring"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[Movie]:
    stmt = select(Movie).order_by(Movie.popularity.desc().nullslast()).limit(limit)
    if q:
        stmt = stmt.where(Movie.title.ilike(f"%{q}%"))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{movie_id}", response_model=MovieDetailOut)
async def get_movie(movie_id: int, session: AsyncSession = Depends(get_session)) -> Movie:
    movie = await session.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movie not found")
    return movie
