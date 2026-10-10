"""Liveness and readiness."""

import re

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.traits import TRAIT_COUNT

router = APIRouter(tags=["health"])

_SHA = re.compile(r"[0-9a-f]{7,40}")


def deployed_commit() -> str | None:
    """The deployed commit's SHA, or None (locally, or anything that is not a SHA).

    Only a hex SHA ever leaves: whatever else the variable held is not echoed. Never
    raises: /health must answer even when the settings cannot be read.
    """
    try:
        commit = get_settings().render_git_commit.strip().lower()
    except Exception:
        return None
    return commit if _SHA.fullmatch(commit) else None


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "trait_dimensions": TRAIT_COUNT, "commit": deployed_commit()}


@router.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
