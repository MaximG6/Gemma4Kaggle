from __future__ import annotations
import os
import re
import time
from pathlib import Path
from typing import Optional

from llama_cpp import Llama

# Resolve model path - check project directory first, then home, then env var
_REPO_ROOT = Path(__file__).resolve().parent.parent
_MODEL_CANDIDATES = [
    _REPO_ROOT / "models" / "voicebridge-finetuned-q4km.gguf",  # Project models dir
    Path.home() / "voicebridge-finetuned-q4km.gguf",  # Home directory fallback
]
FINE_GGUF = os.environ.get("FINE_GGUF")
if not FINE_GGUF or not Path(FINE_GGUF).exists():
    for candidate in _MODEL_CANDIDATES:
        if candidate.exists():
            FINE_GGUF = str(candidate)
            break
    if not FINE_GGUF:
        FINE_GGUF = str(_MODEL_CANDIDATES[0])  # Use first path even if missing (will fail with clear error)
GPU_LAYERS     = 99
THREADS        = 4
TEMP           = 0.1
REPEAT_PENALTY = 1.1
MAX_TOKENS     = 1024
LLAMA_CLI      = None  # Not used; we use llama_cpp Python bindings

LANG_NAMES: dict[str, str] = {
    "en": "English", "sw": "Swahili", "tl": "Tagalog",
    "ha": "Hausa",   "bn": "Bengali", "am": "Amharic",
    "hi": "Hindi",   "fr": "French",
}

_PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "triage_system.txt"
SYSTEM_PROMPT = _PROMPT_FILE.read_text(encoding="utf-8")

_LEVELS = ("red", "orange", "yellow", "green", "blue")

_model: Optional[Llama] = None
_current_model_path: Optional[str] = None

def _get_model(model_path: Optional[str] = None) -> Llama:
    global _model, _current_model_path
    target = model_path or FINE_GGUF
    if _model is None or _current_model_path != target:
        _model = Llama(
            model_path=target,
            n_gpu_layers=GPU_LAYERS,
            n_threads=THREADS,
            n_ctx=4096,
            verbose=False,
        )
        _current_model_path = target
    return _model

def _normalise_level(raw: str) -> Optional[str]:
    if not raw:
        return None
    r = raw.lower().strip()
    return r if r in _LEVELS else None

def build_prompt(text: str, lang: str, system_prompt: Optional[str] = None) -> str:
    sp = (system_prompt or SYSTEM_PROMPT).format(
        lang_name=LANG_NAMES.get(lang, "English")
    )
    return sp

def run_inference(
    model_path: str = "",
    text: str = "",
    lang: str = "en",
    dry_run: bool = False,
    system_prompt: Optional[str] = None,
    temp: Optional[float] = None,
    repeat_penalty: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> tuple[Optional[str], float, str]:
    if dry_run:
        return lang, 0.0, f'{{"triage_level": "{lang}"}}'

    _temp = temp if temp is not None else TEMP
    _rp   = repeat_penalty if repeat_penalty is not None else REPEAT_PENALTY
    _mt   = max_tokens if max_tokens is not None else MAX_TOKENS

    system = (system_prompt or SYSTEM_PROMPT).format(
        lang_name=LANG_NAMES.get(lang, "English")
    )

    t0 = time.time()
    try:
        llm = _get_model(model_path if model_path else None)
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            max_tokens=_mt,
            temperature=_temp,
            repeat_penalty=_rp,
        )
        raw_full = response["choices"][0]["message"]["content"]
    except Exception as exc:
        return None, 0.0, f"[ERROR: {exc}]"

    latency = time.time() - t0
    return None, latency, raw_full
