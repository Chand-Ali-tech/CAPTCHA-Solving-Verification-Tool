# Frontend — CAPTCHA Tool UI (Next.js)

Next.js (App Router + TypeScript) UI for the CAPTCHA Solving & Verification
Tool. It talks to the FastAPI backend in [`../captcha-tool`](../captcha-tool)
through `/api/*`, which is proxied by [`next.config.mjs`](next.config.mjs)
(no CORS, no backend host in the browser bundle).

## Run

```bash
npm install
npm run dev        # http://127.0.0.1:3000
```

The backend must be running on port 8000 (`cd ../captcha-tool && uvicorn app.main:app`).
To point at a different backend, set `BACKEND_URL`:

```bash
BACKEND_URL="http://127.0.0.1:9000" npm run dev
```

## Structure

| Path | Purpose |
|---|---|
| `app/page.tsx` | tab shell; loads backend config, shows a banner if backend is down |
| `app/layout.tsx` | root layout + global styles |
| `app/lib/api.ts` | typed client for every backend endpoint |
| `app/components/SolveTab.tsx` | recognize & solve synthetic / uploaded CAPTCHAs |
| `app/components/ProviderTab.tsx` | detect reCAPTCHA, hCaptcha, Turnstile widgets, and Cloudflare challenge pages from HTML |
| `app/components/VerifyTab.tsx` | live provider test widgets + failure-case testing |
| `app/components/StatsTab.tsx` | batch accuracy run + live dashboard |
| `app/components/CaptchaWidget.tsx` | reusable provider widget (explicit render) |

## Scripts

- `npm run dev` — development server
- `npm run build` — production build
- `npm run start` — serve the production build
- `npm run lint` — Next.js lint
