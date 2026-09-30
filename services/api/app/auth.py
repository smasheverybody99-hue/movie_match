"""Verifying Supabase access tokens (ADR 0007).

Supabase signs access tokens with the project's current JWT signing key: asymmetric
(ES256 or RS256), published as a JWKS at `<project>/auth/v1/.well-known/jwks.json`. The API
checks the signature against that public key, the audience ("authenticated") and the
issuer (`<project>/auth/v1`). It never issues tokens of its own.

The JWKS is cached in the process (PyJWKClient): one download, then reuse for
JWKS_CACHE_SECONDS; a token with an unknown key id triggers one refresh, which is how a
key rotation reaches us. The download is a blocking HTTP call, so it runs in a thread.

HS256 with the legacy shared secret is accepted only while SUPABASE_JWT_SECRET is set.
It is empty by default: after the move to signing keys no live token needs it (ADR 0007).
"""

import asyncio
from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

AUDIENCE = "authenticated"
ASYMMETRIC = frozenset({"ES256", "RS256"})  # what Supabase signing keys use
# Supabase's edge caches the JWKS for 10 minutes; matching that keeps a rotation visible
# within minutes while a busy API downloads the set only a few times an hour.
JWKS_CACHE_SECONDS = 600
JWKS_TIMEOUT_SECONDS = 5


class AuthNotConfigured(Exception):
    """The server cannot verify this kind of token: a setting is missing."""


class AuthKeysUnavailable(Exception):
    """The JWKS could not be downloaded."""


class InvalidToken(Exception):
    """The token does not verify: signature, algorithm, audience, issuer or expiry."""


def jwks_url(project_url: str) -> str:
    return f"{project_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


def issuer(project_url: str) -> str:
    return f"{project_url.rstrip('/')}/auth/v1"


@lru_cache(maxsize=4)
def jwks_client(url: str) -> PyJWKClient:
    """One client per JWKS URL per process, so the key cache is shared by every request."""
    return PyJWKClient(
        url, cache_keys=True, lifespan=JWKS_CACHE_SECONDS, timeout=JWKS_TIMEOUT_SECONDS
    )


async def verify(
    token: str,
    *,
    project_url: str,
    legacy_secret: str = "",
    client: PyJWKClient | None = None,
) -> dict[str, Any]:
    """The verified claims, or an exception saying why not.

    The algorithm is taken from the token header only to choose the verification path;
    each path accepts exactly one family, so a token cannot talk its way from one to the
    other (an HS256 token is never checked against a public key, and "none" is never
    accepted).
    """
    try:
        alg = jwt.get_unverified_header(token).get("alg")
    except jwt.PyJWTError as exc:
        raise InvalidToken(str(exc)) from exc

    if alg in ASYMMETRIC:
        if not project_url:
            raise AuthNotConfigured("SUPABASE_PROJECT_URL is not configured")
        client = client or jwks_client(jwks_url(project_url))
        try:
            key = await asyncio.to_thread(client.get_signing_key_from_jwt, token)
        except jwt.PyJWKClientConnectionError as exc:
            raise AuthKeysUnavailable(str(exc)) from exc
        except jwt.PyJWTError as exc:  # no key with this kid, or a malformed key set
            raise InvalidToken(str(exc)) from exc
        if key.algorithm_name != alg:
            raise InvalidToken(f"token says {alg}, its key is {key.algorithm_name}")
        try:
            return jwt.decode(
                token,
                key.key,
                algorithms=[alg],
                audience=AUDIENCE,
                issuer=issuer(project_url),
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken(str(exc)) from exc

    if alg == "HS256" and legacy_secret:
        try:
            return jwt.decode(token, legacy_secret, algorithms=["HS256"], audience=AUDIENCE)
        except jwt.PyJWTError as exc:
            raise InvalidToken(str(exc)) from exc

    raise InvalidToken(f"algorithm {alg!r} is not accepted")
