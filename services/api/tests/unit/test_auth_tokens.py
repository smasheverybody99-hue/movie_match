"""app.auth.verify against a test key set. No network, no database."""

import base64
import hashlib
import hmac
import json
import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives import serialization

from app import auth
from tests.jwt_keys import (
    ISSUER,
    PROJECT_URL,
    RSA_KEY,
    SIGNING_KEY,
    StaticJWKClient,
    jwks,
    public_jwk,
    token,
)

ME = uuid.uuid4()
LEGACY_SECRET = "legacy-hs256-secret-for-tests-only-0123456789"


async def verify(
    tok: str, client: StaticJWKClient | None = None, *, legacy_secret: str = ""
) -> dict:
    return await auth.verify(
        tok,
        project_url=PROJECT_URL,
        legacy_secret=legacy_secret,
        client=client or StaticJWKClient(),
    )


def test_the_jwks_url_and_issuer_follow_supabase() -> None:
    assert auth.jwks_url("https://abc.supabase.co/") == (
        "https://abc.supabase.co/auth/v1/.well-known/jwks.json"
    )
    assert auth.issuer("https://abc.supabase.co") == "https://abc.supabase.co/auth/v1"


async def test_a_token_signed_with_the_project_key_verifies() -> None:
    claims = await verify(token(ME))
    assert claims["sub"] == str(ME)
    assert claims["aud"] == "authenticated"
    assert claims["iss"] == ISSUER


async def test_an_rs256_signing_key_works_too() -> None:
    client = StaticJWKClient(jwks(public_jwk(RSA_KEY, kid="rsa-1")))
    claims = await verify(token(ME, key=RSA_KEY, algorithm="RS256", kid="rsa-1"), client)
    assert claims["sub"] == str(ME)


@pytest.mark.parametrize(
    "tok",
    [
        pytest.param(token(ME, forged=True), id="forged-same-kid"),
        pytest.param(token(ME, kid="unknown-kid"), id="unknown-kid"),
        pytest.param(token(ME, audience="anon"), id="wrong-audience"),
        pytest.param(token(ME, issuer="https://other.supabase.co/auth/v1"), id="other-project"),
        pytest.param(token(ME, expires_in=-60), id="expired"),
        pytest.param("not.a.jwt", id="garbage"),
    ],
)
async def test_tokens_that_must_not_verify(tok: str) -> None:
    with pytest.raises(auth.InvalidToken):
        await verify(tok)


async def test_alg_none_is_refused() -> None:
    claims = {"sub": str(ME), "aud": "authenticated", "iss": ISSUER, "exp": time.time() + 60}
    unsigned = jwt.encode(claims, None, algorithm="none")  # type: ignore[arg-type]
    with pytest.raises(auth.InvalidToken, match="'none'"):
        await verify(unsigned)


async def test_the_key_type_must_match_the_token_algorithm() -> None:
    """An RS256 key published under the kid an ES256 token names: refused, not guessed."""
    client = StaticJWKClient(jwks(public_jwk(RSA_KEY)))  # same KID, RSA key
    with pytest.raises(auth.InvalidToken, match="ES256"):
        await verify(token(ME), client)


async def test_hs256_is_refused_without_the_legacy_secret() -> None:
    legacy = token(ME, key=LEGACY_SECRET, algorithm="HS256")
    with pytest.raises(auth.InvalidToken, match="HS256"):
        await verify(legacy)


async def test_hs256_is_accepted_only_with_the_legacy_secret_set() -> None:
    legacy = token(ME, key=LEGACY_SECRET, algorithm="HS256")
    assert (await verify(legacy, legacy_secret=LEGACY_SECRET))["sub"] == str(ME)
    with pytest.raises(auth.InvalidToken):
        await verify(
            token(ME, key="another-secret-entirely-0123456789", algorithm="HS256"),
            legacy_secret=LEGACY_SECRET,
        )


async def test_the_public_key_cannot_be_used_as_an_hmac_secret() -> None:
    """Algorithm confusion: HS256 signed with the published public key must not verify."""
    pem = SIGNING_KEY.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )

    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": "test-signing-key-1"}).encode())
    body = b64(
        json.dumps(
            {"sub": str(ME), "aud": "authenticated", "iss": ISSUER, "exp": int(time.time()) + 60}
        ).encode()
    )
    signature = b64(hmac.new(pem, f"{header}.{body}".encode(), hashlib.sha256).digest())
    with pytest.raises(auth.InvalidToken):
        await verify(f"{header}.{body}.{signature}")


async def test_the_key_set_is_downloaded_once_and_reused() -> None:
    client = StaticJWKClient()
    for _ in range(5):
        await verify(token(uuid.uuid4()), client)
    assert client.downloads == 1


async def test_an_unknown_kid_triggers_one_refresh_then_fails() -> None:
    """A rotated-in key reaches us through that refresh; a made-up kid still fails."""
    client = StaticJWKClient()
    await verify(token(ME), client)
    with pytest.raises(auth.InvalidToken):
        await verify(token(ME, kid="rotated-in-later"), client)
    assert client.downloads == 2


async def test_a_newly_rotated_key_is_picked_up() -> None:
    client = StaticJWKClient()
    await verify(token(ME), client)
    client.key_set = jwks(public_jwk(SIGNING_KEY), public_jwk(RSA_KEY, kid="rsa-new"))
    claims = await verify(token(ME, key=RSA_KEY, algorithm="RS256", kid="rsa-new"), client)
    assert claims["sub"] == str(ME)


async def test_an_unreachable_key_set_is_its_own_error() -> None:
    with pytest.raises(auth.AuthKeysUnavailable):
        await verify(token(ME), StaticJWKClient(down=True))


async def test_an_asymmetric_token_without_a_project_url_is_a_configuration_error() -> None:
    with pytest.raises(auth.AuthNotConfigured, match="SUPABASE_PROJECT_URL"):
        await auth.verify(token(ME), project_url="", client=None)


def test_one_cached_client_per_url() -> None:
    first = auth.jwks_client(auth.jwks_url(PROJECT_URL))
    assert auth.jwks_client(auth.jwks_url(PROJECT_URL)) is first
