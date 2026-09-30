"""Request dependencies: authentication, and the explanation generator."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth
from app.config import Settings, get_settings
from app.db import get_session
from app.providers import get_provider
from app.providers.base import Explainer
from app.services.users import ensure_user

_bearer = HTTPBearer(auto_error=False)


def get_jwks_client(settings: Settings = Depends(get_settings)) -> PyJWKClient | None:
    """The project's cached JWKS client; None when SUPABASE_PROJECT_URL is not set.
    Tests override this with a client that serves a test key set without the network."""
    if not settings.supabase_project_url:
        return None
    return auth.jwks_client(auth.jwks_url(settings.supabase_project_url))


async def current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
    jwks: PyJWKClient | None = Depends(get_jwks_client),
) -> uuid.UUID:
    """Verify the Supabase access token and return its subject (app/auth.py, ADR 0007)."""
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    if not settings.supabase_project_url and not settings.supabase_jwt_secret:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "SUPABASE_PROJECT_URL is not configured"
        )

    try:
        payload = await auth.verify(
            creds.credentials,
            project_url=settings.supabase_project_url,
            legacy_secret=settings.supabase_jwt_secret,
            client=jwks,
        )
    except auth.AuthNotConfigured as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)) from exc
    except auth.AuthKeysUnavailable as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Sign-in keys are unavailable, try again"
        ) from exc
    except auth.InvalidToken as exc:
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
    jwks: PyJWKClient | None = Depends(get_jwks_client),
) -> uuid.UUID | None:
    """The caller's id when a token is sent, None when none is.

    For endpoints where auth is optional (TZ §6: film detail). A token that is sent but
    does not verify is still a 401: optional means "may be absent", not "may be forged".
    """
    if creds is None:
        return None
    return await current_user_id(creds, settings, jwks)


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
    """The configured provider's explanation generator, or None without its key
    (explanations then stay null). The provider keeps one client per process."""
    return get_provider(settings).explainer()
