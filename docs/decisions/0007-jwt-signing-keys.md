# ADR 0007 — Verify Supabase tokens with the project's JWKS (ES256), not the HS256 secret

Date: 2026-09-30 · Status: accepted · Amends: ADR 0001 (auth) and CLAUDE.md "Auth"
(still Supabase Auth; only the verification method changes)

## Context

The API verified access tokens with HS256 and the project's shared JWT secret
(`SUPABASE_JWT_SECRET`). The Supabase project has since moved to **JWT Signing Keys**
(user's report from the dashboard, 2026-09-30):

- CURRENT KEY — ECC (P-256), **ES256**, asymmetric
- PREVIOUS KEY — Legacy, HS256

New access tokens are signed with the current key, so the HS256 check would reject every
real sign-in with 401, secret or no secret.

Checked, not assumed:

- Supabase documents the key set at `https://<project>.supabase.co/auth/v1/.well-known/jwks.json`
  and supports ES256, RS256 and HS256 signing keys; after a rotation, non-expired tokens
  signed with the previous key stay valid; the endpoint is edge-cached for 10 minutes
  ([Supabase: JWT Signing Keys](https://supabase.com/docs/guides/auth/signing-keys)).
- `iss` is `https://<project>.supabase.co/auth/v1`, `aud` is `authenticated`
  ([Supabase: JWT fields](https://supabase.com/docs/guides/auth/jwt-fields)).
- The project's own JWKS (fetched once, 2026-09-30) holds one key: `kty` EC, `crv` P-256,
  `alg` ES256, `use` sig, with a `kid`. The HS256 secret is not in it — symmetric keys
  are never published.

## Decision

1. **Verify against the JWKS** (`app/auth.py`), with PyJWT's `PyJWKClient`:
   the token's `kid` picks the public key; the signature, `aud = "authenticated"` and
   `iss = <project>/auth/v1` are checked. Accepted algorithms: ES256 and RS256, and the
   key's own algorithm must equal the token's.
2. **Setting `SUPABASE_PROJECT_URL`** (the same value as the web's `VITE_SUPABASE_URL`).
   The JWKS URL and the issuer are derived from it. No secret is needed.
3. **Keys are cached in the process**: one `PyJWKClient` per URL, key set kept for
   10 minutes (Supabase's own edge cache); a token with an unknown `kid` triggers one
   refresh, which is how a rotation reaches the API. The download is blocking HTTP, so it
   runs in a thread and never stalls the event loop.
4. **Failure is specific**: a bad token is 401; no auth configuration is 500; a JWKS that
   cannot be downloaded is **503** ("Sign-in keys are unavailable, try again") — our
   outage must not look like the user being signed out.
5. **HS256 stays as an opt-in fallback, off by default.** `SUPABASE_JWT_SECRET` is kept;
   only while it is set are HS256 tokens made with it accepted, on their own path (an
   HS256 token is never checked against a public key, so the published key cannot be
   used as an HMAC secret; `none` is never accepted).

## Should both be supported? Assessment

**No — ES256 only in practice; the HS256 path exists but should stay unused, and be
removed once the legacy key is revoked in the dashboard.**

- The only tokens the previous key can verify are access tokens issued before the
  rotation and not yet expired. Supabase access tokens are short-lived (1 hour by
  default), and refreshing issues ES256 tokens. The app has no signed-in users yet, so no
  such token exists; the transition window is already over.
- Keeping the secret set would keep a second way in: anyone holding the legacy secret
  could mint tokens we accept, even after the key is revoked in Supabase, because the API
  would not know. That risk buys nothing.
- It is not deleted in this change because the user asked not to remove the old setting
  at once. Next step: revoke the previous key in the dashboard, then delete the HS256
  path and `SUPABASE_JWT_SECRET` in one commit.

## Consequences

- `.env` needs `SUPABASE_PROJECT_URL`; `SUPABASE_JWT_SECRET` should be empty.
- The first request after start, and one every ~10 minutes after, downloads the JWKS
  (a few hundred bytes). Tests never do: `tests/jwt_keys.py` signs ES256 tokens with a
  key pair made at test time and serves the key set through the real `PyJWKClient`
  with its download step replaced.
- If Supabase moves the project to an RS256 key, nothing changes here; a new algorithm
  family (EdDSA is "coming soon" per the docs) needs one entry in `ASYMMETRIC`.
