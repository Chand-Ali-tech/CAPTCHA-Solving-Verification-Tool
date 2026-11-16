"""
Basic tests. Run with:  pytest

These cover the pieces that don't need network access:
  - synthetic generation + label recovery
  - the OCR solver returns a structured result
  - image recognition classifies a synthetic text CAPTCHA as "text"
  - provider detection from HTML
  - missing-token verification is handled without any network call
"""
import asyncio
from pathlib import Path

import pytest
from captcha.image import ImageCaptcha

from app import recognition, solver, synthetic, verification

# Skip OCR tests when the Tesseract binary isn't installed on this machine.
needs_tesseract = pytest.mark.skipif(
    not solver.tesseract_available(),
    reason="Tesseract OCR binary not installed; install tesseract-ocr to run.")


def _make_png(text="ABCDE") -> bytes:
    return ImageCaptcha(width=220, height=80).generate(text).read()


def test_label_roundtrip():
    assert synthetic.label_from_filename(Path("ABCDE__12ab.png")) == "ABCDE"


@needs_tesseract
def test_solver_structure():
    res = solver.solve_image(_make_png("ABCDE"), expected_length=5)
    assert isinstance(res.text, str)
    assert 0.0 <= res.confidence <= 1.0
    assert res.elapsed_ms >= 0
    assert res.method.startswith("custom-ocr")


def test_recognize_text_image():
    rec = recognition.recognize_image(_make_png("ABCDE"))
    assert rec.challenge_type == "text"
    assert rec.supported is True


def test_recognize_provider_recaptcha():
    html = '<div class="g-recaptcha" data-sitekey="x"></div>'
    rec = recognition.recognize_provider(html)
    assert rec.provider == "recaptcha"
    assert rec.supported is True


def test_recognize_provider_none():
    rec = recognition.recognize_provider("<html><body>hi</body></html>")
    assert rec.provider == "none"


def test_verify_missing_token_no_network():
    res = asyncio.run(verification.verify_token("recaptcha", ""))
    assert res.verified is False
    assert res.status == "missing"
