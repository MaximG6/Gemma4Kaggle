"""
VoiceBridge FastAPI application — full pipeline wiring (Task 2.4).

Endpoints:
  POST /intake          — audio file → TriageOutput JSON + SQLite persistence
  POST /intake/pdf      — audio file → downloadable colour-coded PDF
  GET  /records         — list recent triage records from SQLite
  GET  /records/{id}    — fetch a single record by ID
  GET  /health          — liveness check (reports model load state)

Model loading is deferred to first request so the server starts
instantly even without the model files present (useful for tests).

Run:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import io
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from api.audio_capture import resample_to_16k, router as audio_router
from api.db import get_record, init_db, list_records, save_record
from models.language_id import detect_language_from_audio
from models.transcription import GemmaTranscriber
from pipeline.pdf_generator import generate_triage_pdf
from pipeline.triage import TriageClassifier

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EDGE_MODEL_PATH  = str(_REPO_ROOT / "models" / "gemma4-e4b-it")
_FULL_MODEL_PATH  = str(_REPO_ROOT / "models" / "gemma4-27b-moe")
_FRONTEND_DIR     = _REPO_ROOT / "frontend"

_edge_tx: GemmaTranscriber | None = None
_clf: TriageClassifier | None = None
_models_loaded = False
_load_error: str | None = None


def _load_models() -> None:
    global _edge_tx, _clf, _models_loaded, _load_error
    try:
        edge_path = Path(_EDGE_MODEL_PATH)
        full_path = Path(_FULL_MODEL_PATH)

        if not edge_path.exists():
            raise FileNotFoundError(
                f"Edge model not found at {_EDGE_MODEL_PATH}. "
                "Run: python scripts/download_models.py --e4b"
            )

        _edge_tx = GemmaTranscriber(_EDGE_MODEL_PATH)

        triage_path = full_path if full_path.exists() else edge_path
        triage_tx = GemmaTranscriber(str(triage_path)) if full_path.exists() else _edge_tx
        _clf = TriageClassifier(triage_tx)

        _models_loaded = True
    except Exception as exc:
        _load_error = str(exc)
        raise


def _get_models() -> tuple[GemmaTranscriber, TriageClassifier]:
    """Return loaded models, loading on first call."""
    if not _models_loaded:
        _load_models()
    if _edge_tx is None or _clf is None:
        raise RuntimeError(_load_error or "Models not loaded")
    return _edge_tx, _clf


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="VoiceBridge",
    description="Offline multilingual clinical intake AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(audio_router)

if _FRONTEND_DIR.exists() and any(_FRONTEND_DIR.iterdir()):
    app.mount("/ui", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")


async def _run_intake(file: UploadFile):
    """Shared core: audio file → (record_id, TriageOutput)."""
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    audio = resample_to_16k(raw)
    lang = detect_language_from_audio(audio)

    edge_tx, clf = _get_models()
    tx_result = edge_tx.transcribe(audio, hint_lang=lang)
    triage = clf.classify(tx_result.english_text, source_lang=lang)

    record_id = str(uuid.uuid4())
    return record_id, triage


@app.post("/intake")
async def intake(file: UploadFile, bg: BackgroundTasks):
    """
    Full intake pipeline: audio → TriageOutput JSON.

    - Accepts WAV, MP3, OGG, FLAC (any format librosa supports)
    - Resamples to 16 kHz mono internally
    - Persists result to SQLite in the background
    """
    record_id, triage = await _run_intake(file)
    triage_dict = triage.model_dump(mode="json")
    bg.add_task(save_record, record_id, triage_dict)
    return {"record_id": record_id, "triage": triage_dict}


@app.post("/intake/pdf")
async def intake_pdf(file: UploadFile):
    """
    Full intake pipeline: audio → colour-coded printable PDF.

    Returns a PDF file download (application/pdf).
    """
    _, triage = await _run_intake(file)
    pdf_bytes = generate_triage_pdf(triage)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=triage.pdf"},
    )


@app.get("/records")
def records(limit: int = 50) -> list[dict]:
    """Return the most recent triage records (newest first)."""
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1–500")
    return list_records(limit=limit)


@app.get("/records/{record_id}")
def record_detail(record_id: str) -> dict:
    """Fetch a single triage record by UUID."""
    row = get_record(record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return row


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness + readiness check."""
    return {
        "status": "ok",
        "models_loaded": _models_loaded,
        "load_error": _load_error,
    }
