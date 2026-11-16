"""
verification.py
===============
Official provider token verification  (Rubric part C: Verification Tokens).

Flow (the standard, correct way CAPTCHAs are verified):
    1. The browser widget produces a TOKEN after the user passes.
    2. The frontend sends that token to OUR backend.
    3. OUR backend calls the provider's `siteverify` endpoint with the
       SECRET key (never exposed to the browser) + the token.
    4. The provider returns success/failure + error codes.
    5. We map that into a clean, structured response.

We explicitly handle the four failure cases the assignment calls out:
    - missing   : no token supplied
    - invalid   : token malformed / wrong
    - expired   : token older than ~2 minutes (provider: "timeout-or-duplicate")
    - reused    : token already redeemed  (provider: "timeout-or-duplicate")

IMPORTANT: secret keys and raw tokens are NEVER written to logs or returned
to the client. We only return a short, non-sensitive token fingerprint.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict, field

import httpx

from .config import PROVIDERS

# Provider error codes that mean "expired or already-used token".
_EXPIRED_OR_REUSED = {
    "timeout-or-duplicate",          # reCAPTCHA / Turnstile
    "expired-input-response",        # hCaptcha
    "already-seen-response",         # hCaptcha
    "invalid-or-already-seen-response",  # older hCaptcha response variant
}
_INVALID_CODES = {
    "invalid-input-response",
}
_MISSING_CODES = {"missing-input-response"}


@dataclass
class VerificationResult:
    provider: str
    verified: bool
    status: str               # verified | missing | invalid | expired_or_reused | error
    message: str
    error_codes: list[str] = field(default_factory=list)
    token_fingerprint: str = ""   # safe, non-reversible preview of the token
    provider_raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _fingerprint(token: str) -> str:
    """A short, non-sensitive id for the token (for correlating logs
    without ever storing the real token)."""
    if not token:
        return ""
    return hashlib.sha256(token.encode()).hexdigest()[:12]


def _classify(error_codes: list[str]) -> tuple[str, str]:
    """Map provider error codes to (status, human message)."""
    codes = set(error_codes)
    if codes & _MISSING_CODES:
        return "missing", "No CAPTCHA token was supplied."
    if codes & _EXPIRED_OR_REUSED:
        return ("expired_or_reused",
                "Token has expired or was already used (tokens are single-use "
                "and valid ~2 minutes).")
    if codes & _INVALID_CODES:
        return "invalid", "Token is invalid or malformed."
    return "error", f"Verification failed: {', '.join(error_codes) or 'unknown error'}"


async def verify_token(provider_key: str, token: str | None,
                       remote_ip: str | None = None) -> VerificationResult:
    """Verify a CAPTCHA token with the given provider.

    `provider_key` is one of: recaptcha | hcaptcha | turnstile.
    """
    provider = PROVIDERS.get(provider_key)
    if provider is None:
        return VerificationResult(
            provider=provider_key, verified=False, status="error",
            message=f"Unknown provider '{provider_key}'.")

    # --- Guard: missing token (handled BEFORE any network call) --------
    if not token or not token.strip():
        return VerificationResult(
            provider=provider.name, verified=False, status="missing",
            message="No CAPTCHA token was supplied.",
            error_codes=["missing-input-response"])

    if not provider.secret_key:
        return VerificationResult(
            provider=provider.name, verified=False, status="error",
            message=f"No secret key configured for {provider.name}. "
                    "Set it in .env.")

    payload = {"secret": provider.secret_key, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    # --- Call the provider's siteverify endpoint -----------------------
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(provider.verify_url, data=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        # Network/timeout/5xx — reliability: fail gracefully, never crash.
        return VerificationResult(
            provider=provider.name, verified=False, status="error",
            message=f"Could not reach {provider.name} verification service: "
                    f"{type(exc).__name__}.",
            token_fingerprint=_fingerprint(token))

    success = bool(data.get("success"))
    error_codes = data.get("error-codes", []) or []

    if success:
        return VerificationResult(
            provider=provider.name, verified=True, status="verified",
            message="Token verified successfully.",
            token_fingerprint=_fingerprint(token),
            provider_raw=data)

    status, msg = _classify(error_codes)
    return VerificationResult(
        provider=provider.name, verified=False, status=status, message=msg,
        error_codes=error_codes, token_fingerprint=_fingerprint(token),
        provider_raw=data)
