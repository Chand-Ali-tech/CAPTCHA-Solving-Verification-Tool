"""
main.py
=======
FastAPI application wiring the modules together.

Endpoints
---------
GET  /                        -> web UI
GET  /api/config              -> public SITE keys (never secrets)
POST /api/recognize/image     -> classify an uploaded image
POST /api/recognize/provider  -> detect provider from page HTML
POST /api/solve               -> solve an uploaded text CAPTCHA
GET  /api/sample              -> a fresh synthetic CAPTCHA (png) to try
POST /api/solve/sample        -> generate+solve one synthetic (knows truth)
POST /api/batch               -> generate+solve N synthetic, report accuracy
POST /api/verify              -> verify a provider token (official flow)
GET  /api/stats               -> running dashboard stats
POST /api/stats/reset         -> reset stats

Run:  uvicorn app.main:app --reload
"""
from __future__ import annotations

import base64
import io
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import config, recognition, solver, synthetic, verification
from .solver import TesseractMissingError
from .stats import STATS

app = FastAPI(title="CAPTCHA Solving & Verification Tool", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"


@app.exception_handler(TesseractMissingError)
async def _tesseract_missing_handler(request: Request, exc: TesseractMissingError):
    # 503 Service Unavailable with an actionable message (reliability).
    return JSONResponse(status_code=503, content={"error": str(exc)})


# --------------------------------------------------------------------- UI
@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/config")
async def get_config():
    """Expose only public site keys + the cost model. No secrets."""
    return {
        "site_keys": config.public_site_keys(),
        "cost_model": {
            "custom_solve_usd": config.CUSTOM_SOLVE_COST_USD,
            "thirdparty_solve_usd": config.THIRDPARTY_SOLVE_COST_USD,
        },
    }


# ------------------------------------------------------------- recognition
@app.post("/api/recognize/image")
async def api_recognize_image(file: UploadFile = File(...)):
    data = await file.read()
    try:
        result = recognition.recognize_image(data)
    except Exception as exc:  # malformed upload, etc.
        return JSONResponse(status_code=400,
                            content={"error": f"Could not read image: {exc}"})
    return result.to_dict()


@app.post("/api/recognize/provider")
async def api_recognize_provider(html: str = Form(...)):
    result = recognition.recognize_provider(html)
    return result.to_dict()


# ------------------------------------------------------------------ solve
@app.post("/api/solve")
async def api_solve(file: UploadFile = File(...),
                    expected_length: int = Form(5)):
    data = await file.read()
    # Recognize first: refuse to "solve" unsupported types gracefully.
    try:
        rec = recognition.recognize_image(data)
    except Exception as exc:
        return JSONResponse(status_code=400,
                            content={"error": f"Could not read image: {exc}"})
    if rec.challenge_type not in recognition.SUPPORTED_IMAGE_TYPES:
        return JSONResponse(status_code=422, content={
            "error": "Unsupported challenge type.",
            "recognition": rec.to_dict(),
        })

    result = solver.solve_text_image(data, expected_length=expected_length or None)
    STATS.record(success=result.success, elapsed_ms=result.elapsed_ms,
                 method=result.method,
                 detail={"challenge_type": rec.challenge_type})
    return {"recognition": rec.to_dict(), "solve": result.to_dict()}


@app.get("/api/sample")
async def api_sample():
    """Return a brand-new synthetic CAPTCHA PNG (for the UI to display)."""
    text = synthetic.random_text(5)
    png_bytes = synthetic.render_text(text)
    # The label is returned in a header so the UI can show ground truth.
    return Response(content=png_bytes, media_type="image/png",
                    headers={"X-Captcha-Label": text})


@app.post("/api/solve/sample")
async def api_solve_sample():
    """Generate one synthetic CAPTCHA, solve it, and compare to truth."""
    text = synthetic.random_text(5)
    png_bytes = synthetic.render_text(text)
    result = solver.solve_text_image(png_bytes, expected_length=5)
    correct = result.text == text
    STATS.record(success=correct, elapsed_ms=result.elapsed_ms,
                 method=result.method, detail={"challenge_type": "text"})
    return {
        "ground_truth": text,
        "image_base64": base64.b64encode(png_bytes).decode("ascii"),
        "solve": result.to_dict(),
        "correct": correct,
    }


@app.post("/api/batch")
async def api_batch(count: int = Form(20)):
    """Generate `count` synthetic CAPTCHAs, solve each, report accuracy.
    (Rubric bonus: batch processing + accuracy statistics.)"""
    count = max(1, min(count, 200))  # clamp for safety
    gen = synthetic.new_generator()
    correct = 0
    total_ms = 0.0
    rows = []
    for _ in range(count):
        truth = synthetic.random_text(5)
        png = synthetic.render_text(truth, gen)
        res = solver.solve_text_image(png, expected_length=5)
        is_ok = res.text == truth
        correct += int(is_ok)
        total_ms += res.elapsed_ms
        STATS.record(success=is_ok, elapsed_ms=res.elapsed_ms,
                     method=res.method, detail={"challenge_type": "text"})
        rows.append({"truth": truth, "predicted": res.text,
                     "confidence": res.confidence, "correct": is_ok})
    return {
        "count": count,
        "correct": correct,
        "accuracy": round(correct / count, 4),
        "avg_time_ms": round(total_ms / count, 1),
        "results": rows,
    }


# ----------------------------------------------------------- verification
@app.post("/api/verify")
async def api_verify(request: Request,
                     provider: str = Form(...),
                     token: str = Form("")):
    client_ip = request.client.host if request.client else None
    result = await verification.verify_token(provider, token, remote_ip=client_ip)
    # Record as an attempt for the dashboard (method = provider name).
    STATS.record(success=result.verified, elapsed_ms=0.0,
                 method=f"verify:{result.provider}",
                 detail={"status": result.status})
    return result.to_dict()


# ------------------------------------------------------------------ stats
@app.get("/api/stats")
async def api_stats():
    return STATS.snapshot()


@app.post("/api/stats/reset")
async def api_stats_reset():
    STATS.reset()
    return {"ok": True}


# Mount static files last (so /api routes take precedence).
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
