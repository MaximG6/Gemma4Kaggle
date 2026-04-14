from __future__ import annotations
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Optional

LLAMA_CLI      = str(Path.home() / "llama.cpp" / "build" / "bin" / "llama-cli")
FINE_GGUF      = os.environ.get("FINE_GGUF", str(Path.home() / "voicebridge-finetuned-q4km.gguf"))
GPU_LAYERS     = 99
THREADS        = 4
TEMP           = 0.1
REPEAT_PENALTY = 1.3
MAX_TOKENS     = 1024

LANG_NAMES: dict[str, str] = {
    "en": "English", "sw": "Swahili", "tl": "Tagalog",
    "ha": "Hausa",   "bn": "Bengali", "am": "Amharic",
    "hi": "Hindi",   "fr": "French",
}

_PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "triage_system.txt"
SYSTEM_PROMPT = _PROMPT_FILE.read_text(encoding="utf-8")

_LEVELS = ("red", "orange", "yellow", "green", "blue")


def _normalise_level(raw: str) -> Optional[str]:
    if not raw:
        return None
    r = raw.lower().strip()
    return r if r in _LEVELS else None


def build_prompt(text: str, lang: str, system_prompt: Optional[str] = None) -> str:
    sp = (system_prompt or SYSTEM_PROMPT).format(
        lang_name=LANG_NAMES.get(lang, "English")
    )
    return (
        f"<start_of_turn>system\n{sp}<end_of_turn>\n"
        f"<start_of_turn>user\n{text}<end_of_turn>\n"
        f"<start_of_turn>model\n{{"
    )


def run_inference(
    model_path: str,
    text: str,
    lang: str,
    dry_run: bool = False,
    system_prompt: Optional[str] = None,
    temp: Optional[float] = None,
    repeat_penalty: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> tuple[Optional[str], float, str]:
    if dry_run:
        return lang, 0.0, f'{{"triage_level": "{lang}"}}'

    _temp = temp           if temp           is not None else TEMP
    _rp   = repeat_penalty if repeat_penalty is not None else REPEAT_PENALTY
    _mt   = max_tokens     if max_tokens     is not None else MAX_TOKENS

    prompt   = build_prompt(text, lang, system_prompt)
    tmp_path = Path(f"/tmp/vb_{os.getpid()}_{int(time.time()*1000)}.typescript")

    t0 = time.time()
    try:
        cmd_str = " ".join(shlex.quote(c) for c in [
            LLAMA_CLI, "-m", model_path, "-p", prompt,
            "-n", str(_mt), "--threads", str(THREADS),
            "--temp", str(_temp), "--repeat-penalty", str(_rp),
            "-ngl", str(GPU_LAYERS), "--single-turn", "--log-disable",
        ])
        subprocess.run(
            ["script", "-q", "-c", cmd_str, str(tmp_path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120, check=False,
        )
    except subprocess.TimeoutExpired:
        tmp_path.unlink(missing_ok=True)
        return None, 120.0, "[TIMEOUT]"
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        return None, 0.0, f"[ERROR: {exc}]"

    latency  = time.time() - t0
    raw_full = tmp_path.read_text(errors="replace").strip() if tmp_path.exists() else ""
    tmp_path.unlink(missing_ok=True)

    raw_full = re.sub(r'\x1b\[[0-9;]*[mGKHFABCDJKlh]', '', raw_full)
    raw_full = re.sub(r'\x1b[()][AB012]',               '', raw_full)
    raw_full = re.sub(r'[\r\x00]',                       '', raw_full)

    model_start = raw_full.rfind("<start_of_turn>model")
    search_text = raw_full[model_start:] if model_start != -1 else raw_full

    matches = list(re.finditer(r'"triage_level"\s*:\s*"([^"]+)"', search_text, re.IGNORECASE))
    m = matches[-1] if matches else None
    level = _normalise_level(m.group(1)) if m else None

    return level, latency, raw_full
