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

import os
import sys

# Must be set before `from llama_cpp import Llama` executes anywhere in the
# import chain — ggml_cuda_init runs at that moment and reads this env var.
# RTX 5090 is device 0, RTX 4090 is device 1; restrict to 4090 only.
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

# Print Python identity immediately so we can verify the right env is active.
# The CUDA-enabled llama_cpp will show "CUDA : ARCHS = ..." in its output;
# a CPU-only build shows only "CPU : ...".  If the wrong build appears, the
# server was not started from the voicebridge conda env.
print(f"[VoiceBridge] Python:  {sys.executable}", flush=True)

import io
import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, UploadFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.audio_capture import resample_to_16k, router as audio_router
from api.db import get_record, init_db, list_records, save_record
from models.language_id import detect_language_from_audio
from models.transcription import GemmaTranscriber, TranscriptionResult
from pipeline.llama_infer import FINE_GGUF, LANG_NAMES, SYSTEM_PROMPT, run_inference
from pipeline.pdf_generator import generate_triage_pdf
from pipeline.triage import TriageClassifier

import llama_cpp as _llama_cpp
print(f"[VoiceBridge] llama_cpp: {_llama_cpp.__file__}", flush=True)
print(f"[VoiceBridge] CUDA:      {_llama_cpp.llama_supports_gpu_offload()}", flush=True)

_REPO_ROOT = Path(__file__).resolve().parents[1]
# Use the same GGUF path that llama_infer already resolved: prefers ~/models/ (native
# Linux fs) over /mnt/c/ (DrvFS).  DrvFS mmap pages can't be DMA'd to CUDA, so the
# model silently falls back to CPU unless we load from the native filesystem.
_EDGE_MODEL_PATH  = FINE_GGUF
_FULL_MODEL_PATH  = str(_REPO_ROOT / "models" / "voicebridge-merged-v2")
_FRONTEND_DIR     = _REPO_ROOT / "frontend"
_DASHBOARD_DIR    = _REPO_ROOT / "dashboard"
_BENCHMARK_CASES  = _REPO_ROOT / "data" / "benchmark_cases.json"
print(f"[VoiceBridge] GGUF:      {_EDGE_MODEL_PATH}", flush=True)

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


def _parse_triage_result(raw: str, latency: float, lang: str, raw_transcript: str = "", include_raw: bool = False) -> dict[str, Any]:
    """Parse full triage JSON from raw model output."""
    clean = re.sub(r'\x1b\[[0-9;]*[mGKHFABCDJKlh]', '', raw)
    clean = re.sub(r'\x1b[()][AB012]', '', clean)
    clean = re.sub(r'[\r\x00]', '', clean)

    level = None
    m_level = None
    matches = list(re.finditer(r'"triage_level"\s*:\s*"([^"]+)"', clean, re.IGNORECASE))
    if matches:
        m_level = matches[-1]
        level = m_level.group(1).lower().strip()
        if level not in ("red", "orange", "yellow", "green", "blue"):
            level = None

    result: dict[str, Any] = {
        "triage_level": level or "red",
        "primary_complaint": "",
        "red_flag_indicators": [],
        "recommended_action": "",
        "confidence_score": 0.5,
        "latency_s": round(latency, 2),
        "source_language": lang,
        "referral_needed": False,
        "reported_symptoms": [],
        "vital_signs_reported": {},
        "duration_of_symptoms": "Not recorded",
        "relevant_history": "Not recorded",
        "raw_transcript": raw_transcript,
        "thinking": clean if include_raw else None,
    }

    # Try to extract full JSON
    model_start = clean.rfind("<start_of_turn>model")
    search = clean[model_start:] if model_start != -1 else clean
    start = search.find("{")
    if start != -1:
        end = search.rfind("}") + 1
        js = search[start:end] if end > start else search[start:] + "}"
        js = re.sub(r",\s*}", "}", js)
        js = re.sub(r",\s*]", "]", js)
        try:
            data = json.loads(js)
            if "primary_complaint" in data:
                result["primary_complaint"] = str(data["primary_complaint"])
            if "red_flag_indicators" in data:
                val = data["red_flag_indicators"]
                result["red_flag_indicators"] = val if isinstance(val, list) else []
            if "recommended_action" in data:
                result["recommended_action"] = str(data["recommended_action"])
            if "confidence_score" in data:
                result["confidence_score"] = float(data["confidence_score"])
        except (json.JSONDecodeError, ValueError):
            pass

    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Models will load on first request (deferred).")
    # Pre-load language ID model so the first audio request is not blocked
    from models.language_id import pre_load_lid
    pre_load_lid()
    yield


app = FastAPI(
    title="VoiceBridge",
    description="Offline multilingual clinical intake AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_private_network_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

app.include_router(audio_router)

if _FRONTEND_DIR.exists() and any(_FRONTEND_DIR.iterdir()):
    app.mount("/ui", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")

if _DASHBOARD_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_DASHBOARD_DIR), html=True), name="dashboard")


async def _run_intake(file: UploadFile):
    """
    Shared core: audio file → (record_id, TriageOutput).

    Pipeline:
      1. Resample uploaded audio to 16 kHz mono float32.
      2. Transcribe to text via Gemma 4 native audio tower (base GGUF + mmproj),
         calling llama-mtmd-cli on GPU 1.
      3. Pass transcript to fine-tuned GGUF (TriageClassifier) for SATS triage.
    """
    import soundfile as sf
    import tempfile

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    audio = resample_to_16k(raw)
    lang = detect_language_from_audio(audio)
    duration_s = round(len(audio) / 16000, 2)

    edge_tx, clf = _get_models()

    # Write resampled audio to a temp WAV so llama-mtmd-cli can read it
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        sf.write(tmp_path, audio, 16000)
        transcript = edge_tx.transcribe_audio(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not transcript:
        raise HTTPException(status_code=422, detail="Audio transcription produced empty output.")

    tx_result = TranscriptionResult(
        original_text=transcript,
        english_text=transcript,
        detected_language=lang or "en",
        duration_s=duration_s,
    )
    triage, raw_thinking = clf.classify(tx_result.english_text, source_lang=lang or "en")

    record_id = str(uuid.uuid4())
    return record_id, triage, raw_thinking


@app.post("/intake/text")
async def intake_text(request: Request, bg: BackgroundTasks):
    """
    Text-only intake: plain text → triage JSON via fine-tuned GGUF.

    Request body: {"text": "...", "lang": "en"}
    Returns: triage_level, primary_complaint, red_flag_indicators,
             recommended_action, confidence_score, latency_s, lang
    """
    body = await request.json()
    text = body.get("text", "").strip()
    lang = body.get("lang", "en") or "en"
    if not text:
        raise HTTPException(status_code=400, detail="No text provided.")

    try:
        level, latency, raw = run_inference(text=text, lang=lang)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"TEXT INTAKE ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    result = _parse_triage_result(raw, latency, lang, raw_transcript=text, include_raw=True)
    record_id = str(uuid.uuid4())
    triage_dict = result
    bg.add_task(save_record, record_id, triage_dict)
    return {"record_id": record_id, "triage": triage_dict}


@app.post("/intake/audio")
async def intake_audio(file: UploadFile, bg: BackgroundTasks):
    """
    Audio intake: upload any audio file → triage JSON.

    Accepts WAV, MP3, OGG, FLAC (any format librosa supports).
    Delegates to the shared _run_intake pipeline.
    """
    try:
        record_id, triage, raw_thinking = await _run_intake(file)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    triage_dict = triage.model_dump(mode="json")
    triage_dict["thinking"] = raw_thinking
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
        record_id, triage, raw_thinking = await _run_intake(file)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"INTAKE ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    triage_dict = triage.model_dump(mode="json")
    triage_dict["thinking"] = raw_thinking
    bg.add_task(save_record, record_id, triage_dict)
    return {"record_id": record_id, "triage": triage_dict}


@app.post("/intake/pdf")
async def intake_pdf(file: UploadFile):
    """
    Full intake pipeline: audio → colour-coded printable PDF.

    Returns a PDF file download (application/pdf).
    """
    _, triage, _thinking = await _run_intake(file)
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


@app.get("/benchmark-cases")
def benchmark_cases() -> list:
    """Return the SATS benchmark cases from data/benchmark_cases.json."""
    if not _BENCHMARK_CASES.exists():
        raise HTTPException(status_code=404, detail="benchmark_cases.json not found")
    return json.loads(_BENCHMARK_CASES.read_text(encoding="utf-8"))


_ITERATIVE_SYSTEM_PROMPT = """\
You are a clinical triage assistant (SATS 2023 / WHO ETAT). Your job is to gather enough clinical information to make a safe triage decision.

You have two possible response modes:

MODE 1 — QUESTION: If you do not have enough information to confidently assign a triage level, respond with a single plain-text clarifying question. Ask only the single most important missing piece of information. Do not output JSON in this mode. Do not number the question. Just ask it directly.

MODE 2 — TRIAGE JSON: When you have enough information to make a confident triage decision, output ONLY valid JSON. Your entire response must be a single JSON object with no text before or after it. Example:
{{
  "triage_level": "yellow",
  "primary_complaint": "Moderate headache with visual changes, GCS 15",
  "red_flag_indicators": ["headache", "visual changes"],
  "recommended_action": "Monitor neurological status closely. Urgent review if symptoms worsen.",
  "confidence_score": 0.85
}}

CRITICAL: Use double quotes for all keys and string values. Use [] for empty arrays. Use a float for confidence_score (e.g. 0.85 not 85).

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
    # Handle double braces from prompt escaping
    clean = clean.replace("{{", "{").replace("}}", "}")

    # Try JSON first
    start = clean.find("{")
    if start != -1:
        end = clean.rfind("}") + 1
        js = clean[start:end] if end > start else clean[start:] + "}"
        js = re.sub(r",\s*}", "}", js)
        js = re.sub(r",\s*\]", "]", js)
        try:
            return json.loads(js)
        except json.JSONDecodeError:
            pass

    # Fallback: handle key: value format (no JSON braces)
    result = {}
    m = re.search(r'triage_level\s*:\s*(\w+)', clean, re.IGNORECASE)
    if m:
        result["triage_level"] = m.group(1).lower()
    m = re.search(r'primary_complaint\s*:\s*(.+?)(?=\n\w|\Z)', clean, re.IGNORECASE | re.DOTALL)
    if m:
        result["primary_complaint"] = m.group(1).strip()
    m = re.search(r'recommended_action\s*:\s*(.+?)(?=\n\w|\Z)', clean, re.IGNORECASE | re.DOTALL)
    if m:
        result["recommended_action"] = m.group(1).strip()
    m = re.search(r'confidence_score\s*:\s*([\d.]+)', clean, re.IGNORECASE)
    if m:
        result["confidence_score"] = float(m.group(1))
    m = re.search(r'red_flag_indicators\s*:\s*(\[.*?\])', clean, re.IGNORECASE)
    if m:
        try:
            result["red_flag_indicators"] = json.loads(m.group(1))
        except json.JSONDecodeError:
            result["red_flag_indicators"] = []
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

@app.get("/")
async def root():
    return RedirectResponse(url="/ui")