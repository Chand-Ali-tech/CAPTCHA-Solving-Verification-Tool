"""
synthetic.py
============
Generates a synthetic text-CAPTCHA dataset that WE own and control.

The assignment's scope says: "Only test with synthetic CAPTCHAs, locally
hosted demonstrations, candidate-owned sites, or official provider test
environments." This module is how we stay inside that scope — every image
we solve is one we generated ourselves, with a known ground-truth label.

Each generated file is named "<label>__<id>.png" so the solver's output
can be scored against the real answer for accuracy statistics.
"""
from __future__ import annotations

import random
import string
import uuid
from pathlib import Path

from captcha.image import ImageCaptcha

# Character set: uppercase letters + digits, minus easily-confused chars
# (0/O, 1/I/L) to keep ground-truth labels unambiguous.
ALPHABET = "".join(c for c in (string.ascii_uppercase + string.digits)
                   if c not in "0O1IL")


class ReadableTextCaptcha(ImageCaptcha):
    """Locally owned OCR benchmark images with moderate, controlled variation.

    The defaults rotate letters by up to 30 degrees and add heavy noise. Use
    smaller distortions and faint interference so samples are more CAPTCHA-
    like while remaining suitable for evaluating this project's OCR engine.
    """

    character_offset_dx = (1, 2)
    character_offset_dy = (0, 1)
    character_rotate = (-5, 5)
    character_warp_dx = (0.01, 0.05)
    character_warp_dy = (0.01, 0.04)
    word_space_probability = 0.0
    word_offset_dx = 0.08

    @staticmethod
    def create_noise_dots(image, color, width=1, number=5):
        from PIL import ImageDraw
        import secrets

        draw = ImageDraw.Draw(image)
        w, h = image.size
        for _ in range(number):
            x, y = secrets.randbelow(w), secrets.randbelow(h)
            draw.point((x, y), fill=(205, 205, 205))
        return image

    @staticmethod
    def create_noise_curve(image, color):
        # A light curve adds interference without obscuring the glyph strokes.
        ImageCaptcha.create_noise_curve(image, (210, 210, 210))
        return image


def new_generator() -> ReadableTextCaptcha:
    return ReadableTextCaptcha(width=320, height=100, font_sizes=(36, 42))


def render_text(text: str, generator: ReadableTextCaptcha | None = None) -> bytes:
    """Render a new, OCR-friendly image for this app's own benchmark."""
    generator = generator or new_generator()
    image = generator.generate(
        text, bg_color=(250, 250, 250), fg_color=(25, 25, 25, 255)
    )
    return image.getvalue()


def random_text(length: int = 5) -> str:
    return "".join(random.choice(ALPHABET) for _ in range(length))


def generate_dataset(out_dir: Path, count: int = 50,
                     length: int = 5, seed: int | None = 42) -> list[Path]:
    """Create `count` synthetic CAPTCHA PNGs in `out_dir`.

    Returns the list of file paths created. The ground-truth label is
    embedded in each filename, before the double underscore.
    """
    if seed is not None:
        random.seed(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    generator = new_generator()
    created: list[Path] = []
    for _ in range(count):
        label = random_text(length)
        file_id = uuid.uuid4().hex[:8]
        path = out_dir / f"{label}__{file_id}.png"
        path.write_bytes(render_text(label, generator))
        created.append(path)
    return created


def label_from_filename(path: Path) -> str:
    """Recover the ground-truth label embedded in a filename."""
    return path.name.split("__", 1)[0]


if __name__ == "__main__":
    from .config import SYNTHETIC_DIR
    paths = generate_dataset(SYNTHETIC_DIR, count=50)
    print(f"Generated {len(paths)} synthetic CAPTCHAs in {SYNTHETIC_DIR}")
