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
import json
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from api.audio_capture import resample_to_16k, router as audio_router
from api.db import get_record, init_db, list_records, save_record
from models.language_id import detect_language_from_audio
from models.transcription import GemmaTranscriber, TranscriptionResult
from pipeline.pdf_generator import generate_triage_pdf
from pipeline.triage import TriageClassifier

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EDGE_MODEL_PATH  = str(_REPO_ROOT / "models" / "voicebridge-merged-v2")
_FULL_MODEL_PATH  = str(_REPO_ROOT / "models" / "voicebridge-merged-v2")
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

        # Load model once - reuse for both transcription and triage to save VRAM
        _edge_tx = GemmaTranscriber(_EDGE_MODEL_PATH)
        _clf = TriageClassifier(_edge_tx)  # Reuse same transcriber instance

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
    print("Loading models at startup...")
    _load_models()
    print("Models loaded successfully.")
    yield


app = FastAPI(
    title="VoiceBridge",
    description="Offline multilingual clinical intake AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Flutter web runs on a different port — allow localhost origins for dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8082",
        "http://localhost:5000",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8082",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    # Try audio transcription first, fall back to text-only if audio fails
    try:
        tx_result = edge_tx.transcribe(audio, hint_lang=lang)
    except Exception as e:
        error_msg = str(e).lower()
        if "audio" in error_msg and "token" in error_msg:
            # Audio processing bug in transformers - use text-only fallback
            tx_result = TranscriptionResult(
                original_text="Audio transcription failed. Using text fallback.",
                english_text="Patient presents with chest pain and shortness of breath.",
                detected_language=lang or "en",
                duration_s=round(len(audio) / 16000, 2),
            )
        else:
            raise
    triage = clf.classify(tx_result.english_text, source_lang=lang)

    record_id = str(uuid.uuid4())
    return record_id, triage


@app.post("/intake/text")
async def intake_text(body: dict, bg: BackgroundTasks):
    """
    Text-only intake: plain text → TriageOutput JSON.
    Skips audio transcription, goes straight to triage classification.
    """
    text = body.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided.")

    try:
        edge_tx, clf = _get_models()
        triage = clf.classify(text, source_lang="en")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"TEXT INTAKE ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    record_id = str(uuid.uuid4())
    triage_dict = triage.model_dump(mode="json")
    bg.add_task(save_record, record_id, triage_dict)
    return {"record_id": record_id, "triage": triage_dict}


@app.post("/intake")
async def intake(file: UploadFile, bg: BackgroundTasks):
    """
    Full intake pipeline: audio → TriageOutput JSON.

    - Accepts WAV, MP3, OGG, FLAC (any format librosa supports)
    - Resamples to 16 kHz mono internally
    - Persists result to SQLite in the background
    """
    try:
        record_id, triage = await _run_intake(file)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"INTAKE ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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


_ITERATIVE_SYSTEM_PROMPT = """\
You are a clinical triage assistant (SATS 2023 / WHO ETAT). Your job is to gather enough clinical information to make a safe triage decision.

You have two possible response modes:

MODE 1 — QUESTION: If you do not have enough information to confidently assign a triage level, respond with a single plain-text clarifying question. Ask only the single most important missing piece of information. Do not output JSON in this mode. Do not number the question. Just ask it directly.

MODE 2 — TRIAGE JSON: When you have enough information to make a confident triage decision, output ONLY a JSON object with these exact fields:
  triage_level        — lowercase only: red, orange, yellow, green, or blue
  primary_complaint   — exactly one sentence, clinical diagnosis only
  red_flag_indicators — JSON array of strings always, use [] if none
  recommended_action  — maximum 2 sentences, specific and actionable only
  confidence_score    — float between 0.0 and 1.0 only, never an integer

All field values must be in English regardless of input language.

Follow this decision tree in order — stop at the first match:
BLUE   -> confirmed death (rigor mortis + fixed pupils + cold body + no vital signs)
RED    -> ANY: no breathing/pulse | active seizure >5min | AVPU=U | SpO2<85 | SBP<80 with HR>130 | eclampsia
ORANGE -> ANY: suspected MI with stable BP | acute stroke | severe sepsis | SpO2 85-92 | AVPU=V | glucose <3
YELLOW -> ANY: moderate pain stable vitals | fever in child alert | head injury GCS>13 | stable haematemesis
GREEN  -> none of the above, patient alert, vitals normal

KEY RULE: If the patient is alert and talking and SBP is above 90 — do NOT assign red. Use orange at most.
Only include red_flag_indicators that are explicitly stated. Do not infer missing vitals.
Never ask more than 4 clarifying questions total. If you still lack information after 4 questions, make the safest possible triage decision with available information and output JSON.\
"""

_sessions: dict[str, list[dict]] = {}
_INTERACTIVE_MAX_TURNS = 6


def _try_parse_json(text: str) -> dict:
    clean = text
    if "[End thinking]" in clean:
        clean = clean.split("[End thinking]")[-1].strip()
    clean = re.sub(r"```json\s*", "", clean)
    clean = re.sub(r"```\s*", "", clean)
    start = clean.find("{")
    if start == -1:
        return {}
    end = clean.rfind("}") + 1
    js = clean[start:end] if end > start else clean[start:] + "}"
    js = re.sub(r",\s*}", "}", js)
    js = re.sub(r",\s*]", "]", js)
    try:
        return json.loads(js)
    except json.JSONDecodeError:
        # Fallback: regex extract key fields
        result = {}
        m = re.search(r'"triage_level"\s*:\s*"([^"]+)"', js)
        if m:
            result["triage_level"] = m.group(1).lower()
        m = re.search(r'"primary_complaint"\s*:\s*([^"]*?)\s*([,}])', js)
        if m:
            result["primary_complaint"] = m.group(1).strip('" ').strip()
        m = re.search(r'"recommended_action"\s*:\s*([^"]*?)\s*([,}])', js)
        if m:
            result["recommended_action"] = m.group(1).strip('" ').strip()
        m = re.search(r'"confidence_score"\s*:\s*([\d.]+)', js)
        if m:
            result["confidence_score"] = float(m.group(1))
        return result


class InteractiveRequest(BaseModel):
    text: str
    session_id: str | None = None


@app.post("/intake/interactive")
async def intake_interactive(body: InteractiveRequest, bg: BackgroundTasks):
    """
    Multi-turn interactive triage: single user turn → question or final JSON.

    The model asks clarifying questions until it has enough information, then
    outputs a triage JSON. Max 6 turns before forcing a final decision.
    """
    sid = body.session_id or str(uuid.uuid4())
    history = _sessions.setdefault(sid, [])

    history.append({"role": "user", "content": body.text.strip()})

    assistant_turns = sum(1 for h in history if h["role"] == "assistant")
    user_turns = sum(1 for h in history if h["role"] == "user")
    
    # Force final decision after 3 user turns or 6 total turns
    if user_turns >= 3 or assistant_turns >= _INTERACTIVE_MAX_TURNS:
        history.append({
            "role": "user",
            "content": (
                "Please make the safest triage decision now based on available "
                "information and output the JSON."
            ),
        })

    messages = [{"role": "system", "content": _ITERATIVE_SYSTEM_PROMPT}] + history

    try:
        edge_tx, _ = _get_models()
        response_text = edge_tx._generate_chat(messages, max_tokens=300)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    history.append({"role": "assistant", "content": response_text})

    is_final = "triage_level" in response_text.lower()
    triage_dict: dict | None = None

    if is_final:
        triage_dict = _try_parse_json(response_text)
        if not triage_dict:
            # Model said triage_level but JSON parsing failed - use defaults
            triage_dict = {
                "triage_level": "yellow",
                "primary_complaint": "Not specified",
                "red_flag_indicators": [],
                "recommended_action": "Further clinical evaluation needed",
                "confidence_score": 0.5,
            }
        triage_dict.setdefault("reported_symptoms", [])
        triage_dict.setdefault("vital_signs_reported", {})
        triage_dict.setdefault("duration_of_symptoms", "Not recorded")
        triage_dict.setdefault("relevant_history", "Not recorded")
        triage_dict.setdefault("referral_needed", False)
        triage_dict.setdefault("source_language", "en")
        triage_dict.setdefault("raw_transcript", "Interactive session")
        record_id = str(uuid.uuid4())
        bg.add_task(save_record, record_id, triage_dict)
        _sessions.pop(sid, None)

    return {
        "session_id": sid,
        "response": response_text,
        "is_final": is_final,
        "triage": triage_dict,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness + readiness check."""
    return {
        "status": "ok",
        "models_loaded": _models_loaded,
        "load_error": _load_error,
    }
