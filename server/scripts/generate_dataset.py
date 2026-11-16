#!/usr/bin/env python3
"""
Generate a synthetic CAPTCHA dataset on disk.

Usage:
    python scripts/generate_dataset.py --count 100

Files are written to data/synthetic/ as "<label>__<id>.png".
Run from the project root.
"""
import argparse
import sys
from pathlib import Path

# Make the `app` package importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import SYNTHETIC_DIR      # noqa: E402
from app.synthetic import generate_dataset  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate synthetic CAPTCHAs")
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--length", type=int, default=5)
    args = ap.parse_args()

    paths = generate_dataset(SYNTHETIC_DIR, count=args.count, length=args.length)
    print(f"Generated {len(paths)} synthetic CAPTCHAs in {SYNTHETIC_DIR}")


if __name__ == "__main__":
    main()
