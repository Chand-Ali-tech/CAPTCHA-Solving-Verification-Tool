"""
solver.py
=========
Our CUSTOM CAPTCHA-solving engine (no third-party API).

Pipeline for a text CAPTCHA:
    1. Decode bytes -> grayscale image            (Pillow/OpenCV)
    2. Upscale                                     (helps OCR on small text)
    3. Denoise + threshold (binarize)              (OpenCV)
    4. Morphological "close" to reconnect strokes  (OpenCV)
    5. OCR with a restricted character whitelist   (Tesseract)
    6. Clean the result + compute a confidence     (Tesseract per-char conf)

We return a structured result: the predicted text, a 0..1 confidence,
the elapsed time, and which preprocessing variant won. Several
preprocessing variants are tried and the highest-confidence one wins —
this is a simple but effective reliability trick.
"""
from __future__ import annotations

import io
import re
import time
from dataclasses import dataclass, asdict

import cv2
import numpy as np
import pytesseract
from PIL import Image

# Only allow the characters our synthetic generator can produce.
# (Tesseract does much better when the search space is constrained.)
_WHITELIST = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_TESS_CONFIG = (
    f"--psm 8 --oem 3 -c tessedit_char_whitelist={_WHITELIST}"
)  # psm 8 = treat the image as a single word


class TesseractMissingError(RuntimeError):
    """Raised when the Tesseract OCR binary is not installed/on PATH."""


def tesseract_available() -> bool:
    """True if the Tesseract binary can be found."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


@dataclass
class SolveResult:
    text: str
    confidence: float          # 0.0 .. 1.0
    elapsed_ms: float
    method: str                # e.g. "custom-ocr (variant=otsu)"
    variant: str
    success: bool              # did we read ANY plausible text?

    def to_dict(self) -> dict:
        return asdict(self)


def _to_cv_gray(image_bytes: bytes) -> np.ndarray:
    """Decode arbitrary image bytes into an OpenCV grayscale array."""
    pil = Image.open(io.BytesIO(image_bytes)).convert("L")
    return np.array(pil)


def _preprocess_variants(gray: np.ndarray) -> dict[str, np.ndarray]:
    """Produce several cleaned versions; we OCR each and keep the best."""
    # Upscale 3x — small CAPTCHA text reads far better when enlarged.
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    # Light blur to suppress speckle noise.
    blur = cv2.medianBlur(gray, 3)

    variants: dict[str, np.ndarray] = {}

    # Variant A: Otsu's automatic global threshold.
    _, otsu = cv2.threshold(blur, 0, 255,
                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants["otsu"] = otsu

    # Variant B: inverted Otsu (some CAPTCHAs are light-on-dark).
    variants["otsu_inv"] = cv2.bitwise_not(otsu)

    # Variant C: adaptive threshold (handles uneven backgrounds).
    adaptive = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 25, 10)
    variants["adaptive"] = adaptive

    # Morphological close on the Otsu variant to reconnect broken strokes.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    variants["otsu_closed"] = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)

    return variants


def _ocr_with_confidence(img: np.ndarray) -> tuple[str, float]:
    """Run Tesseract and return (cleaned_text, mean_char_confidence 0..1)."""
    try:
        data = pytesseract.image_to_data(
            img, config=_TESS_CONFIG, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise TesseractMissingError(
            "Tesseract OCR is not installed. Install it with "
            "'sudo apt-get install -y tesseract-ocr' (Debian/Ubuntu), "
            "'brew install tesseract' (macOS), or the UB-Mannheim build "
            "(Windows), then restart the server."
        ) from exc

    chars, confs = [], []
    for txt, conf in zip(data["text"], data["conf"]):
        txt = (txt or "").strip()
        try:
            conf_val = float(conf)
        except (TypeError, ValueError):
            conf_val = -1.0
        if txt and conf_val >= 0:
            chars.append(txt)
            confs.append(conf_val)

    raw = "".join(chars)
    # Keep only whitelisted characters.
    cleaned = re.sub(f"[^{_WHITELIST}]", "", raw.upper())
    mean_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
    return cleaned, round(mean_conf, 4)


def _text_captcha_variants(gray: np.ndarray) -> dict[str, np.ndarray]:
    """Build OCR-friendly views for supported single-line text challenges."""
    enlarged = cv2.resize(gray, None, fx=4, fy=4,
                          interpolation=cv2.INTER_CUBIC)
    # Add a small white border so characters touching the image edge are not
    # clipped by Tesseract's segmentation.
    enlarged = cv2.copyMakeBorder(
        enlarged, 24, 24, 24, 24, cv2.BORDER_CONSTANT, value=255
    )
    contrast = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(enlarged)
    blurred = cv2.GaussianBlur(contrast, (3, 3), 0)
    _, otsu = cv2.threshold(blurred, 0, 255,
                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 9
    )
    return {
        "gray-clahe": contrast,
        "otsu-clahe": otsu,
        "otsu-clahe-inverted": cv2.bitwise_not(otsu),
        "adaptive-clahe": adaptive,
    }


def solve_text_image(image_bytes: bytes,
                     expected_length: int | None = 5) -> SolveResult:
    """OCR a supported single-line text CAPTCHA using several layouts.

    Tesseract confidence alone can favor a short partial reading. A result
    matching the requested expected length gets a modest ranking bonus.
    """
    start = time.perf_counter()
    gray = _to_cv_gray(image_bytes)
    variants = _text_captcha_variants(gray)
    best_text, best_conf, best_variant, best_score = "", 0.0, "none", -1.0

    try:
        for variant_name, img in variants.items():
            for psm in (7, 8, 13):
                config = f"--psm {psm} --oem 3 -c tessedit_char_whitelist={_WHITELIST}"
                try:
                    data = pytesseract.image_to_data(
                        img, config=config, output_type=pytesseract.Output.DICT
                    )
                except pytesseract.TesseractNotFoundError as exc:
                    raise TesseractMissingError(
                        "Tesseract OCR is not installed. Install it with "
                        "'sudo apt-get install -y tesseract-ocr' (Debian/Ubuntu), "
                        "'brew install tesseract' (macOS), or the UB-Mannheim "
                        "build (Windows), then restart the server."
                    ) from exc

                chunks, confidences = [], []
                for raw, confidence in zip(data["text"], data["conf"]):
                    raw = (raw or "").strip()
                    try:
                        confidence = float(confidence)
                    except (TypeError, ValueError):
                        continue
                    if raw and confidence >= 0:
                        chunks.append(raw)
                        confidences.append(confidence)
                text = re.sub(f"[^{_WHITELIST}]", "", "".join(chunks).upper())
                confidence = (sum(confidences) / len(confidences) / 100.0
                              if confidences else 0.0)
                length_bonus = (
                    0.35 if expected_length and len(text) == expected_length else 0.0
                )
                score = confidence + length_bonus
                if score > best_score:
                    best_text, best_conf = text, confidence
                    best_variant, best_score = f"{variant_name}-psm{psm}", score
    except TesseractMissingError:
        raise

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    return SolveResult(
        text=best_text,
        confidence=round(best_conf, 4),
        elapsed_ms=elapsed_ms,
        method=f"custom-ocr-text (variant={best_variant})",
        variant=best_variant,
        success=bool(best_text),
    )


def solve_image(image_bytes: bytes,
                expected_length: int | None = 5) -> SolveResult:
    """Solve one text-CAPTCHA image. Tries every preprocessing variant
    and returns the highest-confidence reading."""
    start = time.perf_counter()
    gray = _to_cv_gray(image_bytes)
    variants = _preprocess_variants(gray)

    best_text, best_conf, best_variant = "", -1.0, "none"
    for name, img in variants.items():
        text, conf = _ocr_with_confidence(img)
        # Prefer readings that match the expected length — a strong signal.
        length_bonus = 0.15 if (expected_length and len(text) == expected_length) else 0.0
        score = conf + length_bonus
        if score > best_conf:
            best_text, best_conf, best_variant = text, conf, name

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    success = bool(best_text)
    return SolveResult(
        text=best_text,
        confidence=max(best_conf, 0.0),
        elapsed_ms=elapsed_ms,
        method=f"custom-ocr (variant={best_variant})",
        variant=best_variant,
        success=success,
    )
