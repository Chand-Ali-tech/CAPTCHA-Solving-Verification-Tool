# CAPTCHA Recognition, Solving and Verification Tool

A web application for exploring CAPTCHA image recognition, OCR-based solving of supported synthetic text challenges, provider widget detection, and server-side verification of provider test tokens. It combines a Next.js frontend with a FastAPI backend and keeps provider secrets on the server.

## Features

- Generate synthetic text CAPTCHA samples and compare OCR predictions with their known answers.
- Upload an image, preview it, classify its likely challenge type, and run OCR when the image is supported.
- Inspect HTML snippets for signatures from Google reCAPTCHA, hCaptcha, Cloudflare Turnstile, or Cloudflare managed challenge pages.
- Verify provider widget tokens through the providers' official `siteverify` endpoints.
- Run batches against generated samples and view accuracy, timing, and method statistics.

The image classifier uses simple image measurements and is intended for demonstration. OCR performance varies with image quality and distortion. Photo-selection challenges are identified as unsupported; the application does not solve them.

## Technology

| Area | Technologies | Purpose |
|---|---|---|
| Frontend | Next.js 14, React 18, TypeScript | Tabbed interface, image upload and preview, provider widgets, and results. |
| Backend | Python, FastAPI, Uvicorn | API routes, application logic, and server-side provider calls. |
| Image processing | Pillow, NumPy, OpenCV | Image decoding, basic classification signals, and OCR preprocessing. |
| OCR | Tesseract OCR through `pytesseract` | Reads supported text CAPTCHA images. Tesseract must also be installed as a system program. |
| Provider verification | `httpx` and provider `siteverify` APIs | Sends tokens and secret keys from the backend for official verification. |

## Project structure

```text
.
├── server/
│   ├── app/
│   │   ├── main.py          FastAPI routes and application wiring
│   │   ├── recognition.py   Image and provider signature recognition
│   │   ├── solver.py        Image preprocessing and OCR
│   │   ├── synthetic.py     Synthetic text CAPTCHA generation
│   │   ├── verification.py  Provider token verification
│   │   ├── stats.py         In-memory run statistics
│   │   └── static/          Minimal backend-served interface
│   ├── requirements.txt
│   └── .env.example
└── client/
    ├── app/
    │   ├── components/      Feature tabs and provider widget
    │   ├── lib/api.ts       Typed API client
    │   └── page.tsx         Main interface
│   ├── next.config.mjs      Server-side proxy for /api requests
│   └── package.json
```

## Run locally

### Prerequisites

- Python 3.10 or newer
- Node.js and npm
- Tesseract OCR installed and available on your `PATH`

On Debian or Ubuntu, install Tesseract with:

```bash
sudo apt-get install tesseract-ocr
```

On macOS, use `brew install tesseract`. On Windows, install a Tesseract build and make sure its executable is on `PATH`.

### Start the backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. The backend's `.env.example` provides the configuration names and development defaults. Keep any real provider secret keys in `server/.env`; do not expose them in frontend code or commit them.

### Start the frontend

In a second terminal:

```bash
cd client
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. The frontend forwards `/api/*` requests to the backend at `http://127.0.0.1:8000` by default. To use another backend URL, set `BACKEND_URL` when running or building the frontend.

## Application flow

```text
Browser
  │
  ▼
Next.js interface ── /api proxy ──► FastAPI
                                      ├── Recognition
                                      ├── OCR solver
                                      ├── Synthetic generator
                                      ├── Provider verification
                                      └── Statistics
```

For an image upload, the backend first checks whether the image resembles a supported text challenge. If supported, it creates OCR-friendly image variants and evaluates them with Tesseract. For a generated sample, the known text is available to report correctness. Uploaded images do not include a known answer, so their correctness cannot be automatically scored.

For provider verification, the frontend sends a provider name and token to the backend. The backend uses its configured secret to call the provider's verification endpoint and returns a structured result. Public site keys may be sent to the browser to render widgets; secret keys stay server-side.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/config` | Returns public widget keys and cost settings. |
| `POST` | `/api/recognize/image` | Classifies an uploaded image. |
| `POST` | `/api/recognize/provider` | Checks HTML for provider signatures. |
| `POST` | `/api/solve` | Recognizes and runs OCR on a supported uploaded image. |
| `GET` | `/api/sample` | Returns a generated sample image. |
| `POST` | `/api/solve/sample` | Generates and solves one sample, including correctness. |
| `POST` | `/api/batch` | Measures results over generated samples. |
| `POST` | `/api/verify` | Verifies a provider token server-side. |
| `GET` | `/api/stats` | Returns in-memory run statistics. |
| `POST` | `/api/stats/reset` | Resets in-memory run statistics. |

## Production frontend build

```bash
cd client
npm run build
npm run start
```

Set `BACKEND_URL` to the intended FastAPI server address for the deployment environment.

## Limitations

- OCR is a conventional Tesseract pipeline; accuracy depends on the image and preprocessing and is not guaranteed.
- Image type classification is heuristic and may return `unknown` for ambiguous images.
- Provider recognition inspects supplied HTML signatures; it does not load or execute the page.
- Dashboard statistics are held in memory and reset when the backend restarts.
- Provider token verification requires correctly configured provider keys and network access to the provider endpoint.
