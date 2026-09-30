"""Supabase-shaped access tokens for tests, signed with a key pair made here.

No network: StaticJWKClient is the real PyJWKClient (key lookup by kid, caching) with
the one method that downloads the key set replaced by returning ours.
"""

import json
import time
import uuid
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from jwt import PyJWKClient
from jwt.algorithms import ECAlgorithm, RSAAlgorithm

from app import auth

PROJECT_URL = "https://test-project.supabase.co"
ISSUER = auth.issuer(PROJECT_URL)
KID = "test-signing-key-1"

# The project's key, and a stranger's key used to forge tokens with the same kid.
SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
FORGER_KEY = ec.generate_private_key(ec.SECP256R1())
RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def public_jwk(private_key: Any, kid: str = KID) -> dict[str, Any]:
    if isinstance(private_key, rsa.RSAPrivateKey):
        jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
        jwk["alg"] = "RS256"
    else:
        jwk = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
        jwk["alg"] = "ES256"
    return {**jwk, "kid": kid, "use": "sig", "key_ops": ["verify"]}


def jwks(*keys: dict[str, Any]) -> dict[str, Any]:
    return {"keys": list(keys) or [public_jwk(SIGNING_KEY)]}


class StaticJWKClient(PyJWKClient):
    """PyJWKClient over a fixed key set. Counts downloads, can simulate an outage."""

    def __init__(self, key_set: dict[str, Any] | None = None, *, down: bool = False) -> None:
        super().__init__(
            auth.jwks_url(PROJECT_URL), cache_keys=True, lifespan=auth.JWKS_CACHE_SECONDS
        )
        self.key_set = key_set or jwks()
        self.down = down
        self.downloads = 0

    def fetch_data(self) -> Any:
        self.downloads += 1
        if self.down:
            raise jwt.PyJWKClientConnectionError("Fail to fetch data from the url, err: down")
        return self.key_set


def token(
    user_id: uuid.UUID | str | None,
    *,
    forged: bool = False,
    audience: str = "authenticated",
    issuer: str = ISSUER,
    expires_in: int = 3600,
    key: Any = None,
    algorithm: str = "ES256",
    kid: str = KID,
) -> str:
    """A Supabase access token: ES256, the project's kid, aud and iss as Supabase sets them."""
    now = int(time.time())
    claims: dict[str, Any] = {
        "aud": audience,
        "iss": issuer,
        "iat": now,
        "exp": now + expires_in,
        "role": "authenticated",
    }
    if user_id is not None:
        claims["sub"] = str(user_id)
    signer = key if key is not None else (FORGER_KEY if forged else SIGNING_KEY)
    return jwt.encode(claims, signer, algorithm=algorithm, headers={"kid": kid})
