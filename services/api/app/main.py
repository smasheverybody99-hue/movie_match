"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, movies

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup work goes here (warm caches, check migrations). Keep it fast.
    yield
    from app.db import engine

    await engine.dispose()


app = FastAPI(
    title="Movie Match API",
    version="0.1.0",
    description="AI-powered movie discovery.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(movies.router)
