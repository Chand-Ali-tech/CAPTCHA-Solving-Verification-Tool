# CAPTCHA Solving & Verification Tool

A standalone application that **recognizes**, **solves**, and **verifies**
CAPTCHA challenges in an authorized test environment.

- **Frontend** — Next.js (App Router + TypeScript), in [`frontend/`](frontend/).
- **Backend** — FastAPI (Python) with a custom OpenCV + Tesseract OCR solver
  and official provider token verification, in [`captcha-tool/`](captcha-tool/).

The Next.js UI calls the backend through `/api/*`, which Next proxies to the
FastAPI server (see [`frontend/next.config.mjs`](frontend/next.config.mjs)) —
so there is no CORS setup and no backend host baked into the browser bundle.

> **Scope & ethics.** Tested only against synthetic CAPTCHAs we generate and
> the providers' official public **test keys**. It does **not** automate
> third-party contact forms, submit to real sites, or bypass anti-bot
> protection on sites we don't own — consistent with the assignment scope.

---

## Project layout

```
Challange/
├── captcha-tool/      FastAPI backend (Python)
│   ├── app/           recognition, solver, synthetic, verification, stats, main
│   ├── requirements.txt
│   └── README.md      ← backend details: API reference, cost breakdown, env vars
└── frontend/          Next.js frontend (TypeScript)
    ├── app/
    │   ├── page.tsx         tab shell + backend config
    │   ├── components/      one component per feature tab + CaptchaWidget
    │   └── lib/api.ts       typed backend client
    └── next.config.mjs      proxies /api/* to the backend
```

---

## Architecture

```
Browser ──► Next.js UI (port 3000)
                │  fetch("/api/...")
                │  (Next.js rewrite proxies to the backend)
                ▼
            FastAPI backend (port 8000)
                ├─ recognition  (challenge type + provider widget)
                ├─ solver       (OpenCV preprocessing → Tesseract OCR → confidence)
                ├─ synthetic    (owned CAPTCHA generator, ground-truth labels)
                ├─ verification (provider /siteverify with the SECRET key)
                └─ stats        (attempts / success / time / cost)
```

---

## Run it (two terminals)

### Terminal 1 — backend (FastAPI)
```bash
cd captcha-tool
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
sudo apt-get install -y tesseract-ocr               # the OCR engine (macOS: brew install tesseract)
cp .env.example .env                                # defaults are official test keys — ready to run
uvicorn app.main:app --reload                       # http://127.0.0.1:8000
```

### Terminal 2 — frontend (Next.js)
```bash
cd frontend
npm install
npm run dev                                          # http://127.0.0.1:3000
```

Open **http://127.0.0.1:3000**. If the red banner says the backend is
unreachable, make sure Terminal 1 is running.

> The backend also still serves a minimal fallback UI at
> http://127.0.0.1:8000 — handy if you ever want to demo without Node.

---

## Features (mapped to the rubric)

| Rubric criterion | Weight | Where |
|---|---|---|
| Recognition / solving accuracy | 30% | `captcha-tool/app/recognition.py`, `solver.py` |
| Verification-token handling | 20% | `captcha-tool/app/verification.py` |
| Custom AI / API integration | 20% | `solver.py` (OpenCV + Tesseract) |
| Reliability & error handling | 15% | graceful errors; best-of-N solving; 503 on missing Tesseract |
| Interface & reporting | 10% | Next.js app + `stats.py` dashboard |
| Code quality & documentation | 5% | typed components, docstrings, tests, this README |

**Bonus implemented:** three providers, batch accuracy stats, a reusable JSON
API, and a best-of-N preprocessing fallback.

See [`captcha-tool/README.md`](captcha-tool/README.md) for backend-specific
details (full API reference, cost breakdown, env vars, demo script) and
[`frontend/README.md`](frontend/README.md) for frontend notes.

---

## Production build (frontend)
```bash
cd frontend
npm run build && npm run start        # serves the optimized Next.js app
```
Point the UI at a non-local backend by setting `BACKEND_URL` before building:
```bash
BACKEND_URL="https://your-backend.example.com" npm run build
```
