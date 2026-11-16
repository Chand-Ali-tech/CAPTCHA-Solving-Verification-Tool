"""
recognition.py
==============
"What kind of CAPTCHA is this?"  (Rubric part A: CAPTCHA Recognition.)

Two kinds of recognition:

1. IMAGE recognition  -> classify an uploaded image as:
   - "text"      : a synthetic text CAPTCHA  (SUPPORTED by our solver)
   - "image_grid": a "select all squares with..." style  (UNSUPPORTED)
   - "unknown"
   This lets us "distinguish recognized challenge types from unsupported
   ones" as the assignment requires.

2. PROVIDER recognition -> given a page's HTML (from an OWNED test page or
   an official provider demo), detect which widget is embedded:
   Google reCAPTCHA, hCaptcha, Cloudflare Turnstile, or a Cloudflare-managed
   challenge page.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, asdict

import numpy as np
from PIL import Image

SUPPORTED_IMAGE_TYPES = {"text"}


@dataclass
class ImageRecognition:
    challenge_type: str      # text | image_grid | unknown
    supported: bool
    reason: str
    width: int
    height: int

    def to_dict(self) -> dict:
        return asdict(self)


def recognize_image(image_bytes: bytes) -> ImageRecognition:
    """Heuristic image classifier.

    Text CAPTCHAs are typically short and wide (one line of characters).
    Image-grid CAPTCHAs are roughly square and visually busy (photos).
    We use aspect ratio + a simple "edge density" measure as signals.
    """
    pil = Image.open(io.BytesIO(image_bytes)).convert("L")
    w, h = pil.size
    arr = np.array(pil)

    aspect = w / h if h else 0
    # Edge density: fraction of pixels that are strong gradients.
    gy, gx = np.gradient(arr.astype(float))
    edges = np.hypot(gx, gy)
    edge_density = float((edges > 40).mean())

    # Wide + modest edge density => a line of text.
    if aspect >= 1.8 and edge_density < 0.35:
        return ImageRecognition(
            "text", True,
            f"wide aspect ratio ({aspect:.1f}) with text-like edge density "
            f"({edge_density:.2f}) — looks like a single line of characters.",
            w, h)

    # Near-square + very busy => photographic grid (unsupported).
    if 0.7 <= aspect <= 1.4 and edge_density >= 0.35:
        return ImageRecognition(
            "image_grid", False,
            f"near-square aspect ({aspect:.1f}) with high edge density "
            f"({edge_density:.2f}) — looks like a photo selection grid, "
            f"which this tool does not solve.",
            w, h)

    return ImageRecognition(
        "unknown", False,
        f"could not confidently classify (aspect {aspect:.1f}, "
        f"edge density {edge_density:.2f}).",
        w, h)


# --- Provider widget detection ----------------------------------------

# Signature patterns keyed by provider. We look at raw page HTML.
_PROVIDER_SIGNATURES: dict[str, list[re.Pattern]] = {
    "recaptcha": [
        re.compile(r"(?:google\.com|recaptcha\.net)/recaptcha", re.I),
        re.compile(r"gstatic\.com/recaptcha", re.I),
        re.compile(r'\bclass\s*=\s*["\'][^"\']*\bg-recaptcha\b', re.I),
        re.compile(r'\bname\s*=\s*["\']g-recaptcha-response["\']', re.I),
        re.compile(r"grecaptcha", re.I),
    ],
    "hcaptcha": [
        re.compile(r"(?:js\.)?hcaptcha\.com", re.I),
        re.compile(r'\bclass\s*=\s*["\'][^"\']*\bh-captcha\b', re.I),
        re.compile(r'\bname\s*=\s*["\']h-captcha-response["\']', re.I),
    ],
    "turnstile": [
        re.compile(r"challenges\.cloudflare\.com/turnstile", re.I),
        re.compile(r'\bclass\s*=\s*["\'][^"\']*\bcf-turnstile\b', re.I),
        re.compile(r'\bname\s*=\s*["\']cf-turnstile-response["\']', re.I),
    ],
}

# "invisible" reCAPTCHA hint (seen in the CSV dataset's Captcha column).
_INVISIBLE_RECAPTCHA = re.compile(r'data-size=["\']invisible', re.I)


@dataclass
class ProviderRecognition:
    provider: str            # provider name, cloudflare_challenge, multiple, or none
    invisible: bool
    matched_signals: list[str]
    supported: bool
    verification_supported: bool

    def to_dict(self) -> dict:
        return asdict(self)


def recognize_provider(html: str) -> ProviderRecognition:
    """Detect a provider widget or a Cloudflare-managed challenge page.

    A Cloudflare interstitial is not necessarily a Turnstile widget. In
    particular, its challenge-platform markup differs from Turnstile's
    ``cf-turnstile`` element and siteverify flow, so report it separately.
    """
    hits_by_provider = {
        provider: [pattern.pattern for pattern in patterns if pattern.search(html)]
        for provider, patterns in _PROVIDER_SIGNATURES.items()
    }
    detected = [provider for provider, hits in hits_by_provider.items() if hits]

    if len(detected) == 1:
        found = detected[0]
        matched = hits_by_provider[found]
    elif len(detected) > 1:
        found = "multiple"
        matched = [signal for provider in detected for signal in hits_by_provider[provider]]
    else:
        # Cloudflare interstitials may not contain a Turnstile widget URL or
        # class. Their challenge-platform route is the strongest signature.
        cloudflare_challenge_signals = [
            re.compile(r"/cdn-cgi/challenge-platform(?:/|\b)", re.I),
            re.compile(r"__cf_chl_|cf_chl_", re.I),
        ]
        challenge_hits = [
            pattern.pattern for pattern in cloudflare_challenge_signals
            if pattern.search(html)
        ]
        has_challenge_error = bool(re.search(r"challenge-error-text", html, re.I))
        has_cloudflare_brand = bool(re.search(r"cloudflare\.com", html, re.I))
        if challenge_hits or (has_challenge_error and has_cloudflare_brand):
            found = "cloudflare_challenge"
            matched = challenge_hits
            if has_challenge_error:
                matched.append("challenge-error-text")
            if has_cloudflare_brand:
                matched.append("cloudflare.com")
        else:
            found = "none"
            matched = []

    invisible = bool(_INVISIBLE_RECAPTCHA.search(html)) and found == "recaptcha"
    supported = found in {
        "recaptcha", "hcaptcha", "turnstile", "cloudflare_challenge", "multiple"
    }
    verification_supported = found in {"recaptcha", "hcaptcha", "turnstile"}
    return ProviderRecognition(
        found, invisible, matched, supported, verification_supported
    )
