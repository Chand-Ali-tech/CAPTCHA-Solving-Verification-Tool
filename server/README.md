# CAPTCHA Solving & Verification Tool

A standalone application that **recognizes** CAPTCHA challenges, **solves**
supported (synthetic text) CAPTCHAs with a custom OCR engine, and performs
**official token verification** against Google reCAPTCHA, hCaptcha, and
Cloudflare Turnstile — all inside an authorized test environment.

> **Scope & ethics.** This tool is tested **only** against synthetic
> CAPTCHAs we generate ourselves and the CAPTCHA providers' **official
> public test keys**. It does **not** automate third-party contact forms,
> submit to real websites, or bypass anti-bot protection on sites we don't
> own — consistent with the assignment's stated scope (Section 7).

---

## 1. What it does (mapped to the rubric)

| Rubric criterion | Weight | Where it lives |
|---|---|---|
| Recognition / solving accuracy | 30% | [`app/recognition.py`](app/recognition.py), [`app/solver.py`](app/solver.py) |
| Verification-token handling | 20% | [`app/verification.py`](app/verification.py) |
| Custom AI / API integration | 20% | [`app/solver.py`](app/solver.py) (OpenCV + Tesseract OCR) |
| Reliability & error handling | 15% | graceful failures throughout; multi-variant solving |
| Interface & reporting | 10% | [`app/static/index.html`](app/static/index.html), [`app/stats.py`](app/stats.py) |
| Code quality & docs | 5% | this README + inline docstrings + `tests/` |

**Bonus features implemented:** multiple providers, batch processing with
accuracy statistics, a reusable JSON API, and best-of-N preprocessing as a
fallback strategy.

---

## 2. Architecture

```
Browser UI (static/index.html)
        │  (fetch / FormData)
        ▼
FastAPI backend (app/main.py)
   ├── recognition.py   image type + provider-widget detection
   ├── solver.py        custom OCR: OpenCV preprocessing → Tesseract → confidence
   ├── synthetic.py     generates owned CAPTCHA images (ground-truth labels)
   ├── verification.py  calls provider /siteverify with SECRET key (server-side)
   ├── stats.py         running attempts / success / time / cost
   └── config.py        loads all keys from .env (no hard-coded secrets)
```

**Solving pipeline:** after image recognition accepts a text challenge, the
solver enlarges it with a white border, enhances local contrast, tries
grayscale and thresholded views with Tesseract's line/word segmentation
modes, and ranks readings with a modest expected-length bonus. The app's
own benchmark images use `ReadableTextCaptcha`: randomized text with mild
rotations and warping, plus sparse faint dots and a light interference curve.
The upstream generator's default strong rotations, warping, and noise
overwhelmed this basic OCR pipeline, so the custom generator applies a
moderate level of distortion that remains useful for OCR evaluation.
Generated samples are compared against their known label; uploaded images do
not have ground truth, so their OCR accuracy cannot be reported automatically.

**Verification flow:** the browser widget yields a token → frontend POSTs it
to our backend → backend calls the provider's `siteverify` endpoint with the
**secret key** → we return a structured result. Secret keys and raw tokens
are never exposed to the client or written to logs (only a short SHA-256
fingerprint of the token is surfaced).

---

## 3. Setup

### Prerequisites
- Python 3.10+
- **Tesseract OCR engine** (the system binary — `pytesseract` is only a wrapper):
  - Debian/Ubuntu: `sudo apt-get install -y tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: install from the UB-Mannheim build, add it to PATH.

### Install
```bash
cd captcha-tool
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # the defaults are official test keys — ready to run
```

### Run
```bash
uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```

### Optional: pre-generate a dataset on disk
```bash
python scripts/generate_dataset.py --count 100
```

### Run tests
```bash
pytest
```

---

## 4. Environment variables

All configured in `.env` (see `.env.example`). Defaults are the providers'
**official public test keys**, which always pass verification — ideal for a
demo and safe to share.

| Variable | Purpose |
|---|---|
| `RECAPTCHA_SITE_KEY` / `RECAPTCHA_SECRET_KEY` | Google reCAPTCHA v2 |
| `HCAPTCHA_SITE_KEY` / `HCAPTCHA_SECRET_KEY` | hCaptcha |
| `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile |
| `CUSTOM_SOLVE_COST_USD` | cost per solve for our engine (0 — it's free) |
| `THIRDPARTY_SOLVE_COST_USD` | illustrative cost if a paid API were used |

> Secret keys live only in `.env`, which is git-ignored. Never commit a real
> secret key.

---

## 5. API reference (reusable endpoints)

| Method & path | Body | Returns |
|---|---|---|
| `GET /api/config` | – | public site keys + cost model |
| `POST /api/recognize/image` | file | challenge type + supported flag |
| `POST /api/recognize/provider` | `html` | detected provider |
| `POST /api/solve` | file, `expected_length` | recognition + solved text + confidence |
| `GET /api/sample` | – | a fresh synthetic PNG (label in `X-Captcha-Label`) |
| `POST /api/solve/sample` | – | generate+solve one, with correctness |
| `POST /api/batch` | `count` | accuracy over N synthetic CAPTCHAs |
| `POST /api/verify` | `provider`, `token` | structured verification result |
| `GET /api/stats` | – | dashboard totals |

Verification `status` values: `verified`, `missing`, `invalid`,
`expired_or_reused`, `error`.

---

## 6. Cost breakdown

| Method | Cost per solve | Notes |
|---|---|---|
| **Custom OCR (default)** | **$0.00** | OpenCV + Tesseract, runs locally, no API |
| Third-party API (optional) | ~$0.001–0.003 | e.g. 2Captcha ≈ $1–3 per 1,000 solves; not used by default |

Token **verification** with the providers is **free** — `siteverify` is a
free API call for all three providers.

---

## 7. Demo script (for the 3–5 min video)

1. **Tab 1 – Solve:** click *Generate & solve* a few times → show predicted
   text, confidence, time vs. ground truth. Upload an image → show it
   recognizing type before solving.
2. **Tab 2 – Provider recognition:** run the local reCAPTCHA, hCaptcha, and
   Turnstile HTML examples; paste the owned page's markup to inspect detected
   signatures. Cloudflare managed challenge pages are identified separately.
3. **Tab 3 – Verification (success):** solve each live test widget → show
   `VERIFIED`. **(Failure):** click *missing* and *invalid* → show the
   graceful, structured error statuses.
4. **Tab 4 – Batch & dashboard:** run a batch of 50 → show the accuracy
   figure and the live stats tiles (attempts / success / time / cost).

---

## 8. Limitations & honest notes

- The OCR solver targets **synthetic text CAPTCHAs**. Heavily obfuscated or
  photo-grid ("select all buses") challenges are **recognized as
  unsupported**, not solved — by design and within scope.
- Accuracy depends on the Tesseract version and the distortion level of the
  generated images; the best-of-N variant strategy improves robustness but
  does not make it perfect. The dashboard reports the real measured number.
- Provider test keys always pass; to demo a genuine *fail* from a provider,
  use Turnstile's always-fails secret `2x0000000000000000000000000000000AA`.
```
