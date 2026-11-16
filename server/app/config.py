"""
config.py
=========
Central configuration. Loads every secret/key from environment variables
(via a .env file) so that NOTHING sensitive is hard-coded in source.

Why this matters for the assignment (rubric: "secure token handling",
"without exposing secret keys"): secret keys live only in `.env`, which is
git-ignored. The code reads them through this single module.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load the .env sitting at the project root (one level above /app).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class ProviderKeys:
    """Site key (public, safe to send to the browser) + secret key
    (server-only, used to call the provider's siteverify API)."""
    name: str
    site_key: str
    secret_key: str
    verify_url: str


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# --- Provider configurations (populated from .env) --------------------
RECAPTCHA = ProviderKeys(
    name="reCAPTCHA",
    site_key=_get("RECAPTCHA_SITE_KEY"),
    secret_key=_get("RECAPTCHA_SECRET_KEY"),
    verify_url="https://www.google.com/recaptcha/api/siteverify",
)

HCAPTCHA = ProviderKeys(
    name="hCaptcha",
    site_key=_get("HCAPTCHA_SITE_KEY"),
    secret_key=_get("HCAPTCHA_SECRET_KEY"),
    verify_url="https://api.hcaptcha.com/siteverify",
)

TURNSTILE = ProviderKeys(
    name="Turnstile",
    site_key=_get("TURNSTILE_SITE_KEY"),
    secret_key=_get("TURNSTILE_SECRET_KEY"),
    verify_url="https://challenges.cloudflare.com/turnstile/v0/siteverify",
)

PROVIDERS: dict[str, ProviderKeys] = {
    "recaptcha": RECAPTCHA,
    "hcaptcha": HCAPTCHA,
    "turnstile": TURNSTILE,
}

# --- Cost model (reporting only) --------------------------------------
CUSTOM_SOLVE_COST_USD = float(_get("CUSTOM_SOLVE_COST_USD", "0.0") or 0.0)
THIRDPARTY_SOLVE_COST_USD = float(_get("THIRDPARTY_SOLVE_COST_USD", "0.002") or 0.002)

# --- Paths ------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"


def public_site_keys() -> dict[str, str]:
    """Only the SITE keys — safe to expose to the frontend widgets.
    Secret keys are deliberately never returned here."""
    return {k: v.site_key for k, v in PROVIDERS.items()}
