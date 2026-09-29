"""Request dependencies: authentication, and the explanation generator."""

import uuid
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_session
from app.services.explain import Explainer, GeminiExplainer
from app.services.users import ensure_user

_bearer = HTTPBearer(auto_error=False)


async def current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> uuid.UUID:
    """Verify the Supabase access token and return its subject.

    Supabase signs access tokens with the project's JWT secret (HS256).
    The API never issues tokens of its own.
    """
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "SUPABASE_JWT_SECRET is not configured"
        )

    try:
        payload = jwt.decode(
            creds.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has no subject")

    try:
        return uuid.UUID(str(sub))
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token subject is not a user id") from exc


async def optional_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> uuid.UUID | None:
    """The caller's id when a token is sent, None when none is.

    For endpoints where auth is optional (TZ §6: film detail). A token that is sent but
    does not verify is still a 401: optional means "may be absent", not "may be forged".
    """
    if creds is None:
        return None
    return await current_user_id(creds, settings)


async def current_user(
    user_id: uuid.UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> uuid.UUID:
    """The caller's id, with their local `users` row created on first sight.

    Supabase is the identity source; our table mirrors it so ratings have a user to
    belong to.
    """
    await ensure_user(session, user_id)
    return user_id


def get_explainer(settings: Settings = Depends(get_settings)) -> Explainer | None:
    """The explanation generator, or None without a Gemini key (explanations stay null)."""
    if not settings.gemini_api_key:
        return None
    return _explainer(settings.gemini_api_key)


@lru_cache
def _explainer(api_key: str) -> Explainer:
    """One client per process (per key), not one per request."""
    from google import genai

    return GeminiExplainer(genai.Client(api_key=api_key).aio)
