"""
Gemma 4 transcription wrapper — audio/text to structured triage output.

Uses llama-cpp-python with the quantized GGUF model (text decoder) for
language normalisation and structured output.  Audio transcription uses
GemmaAudioTranscriber (models/audio_transcriber.py), which calls
llama-mtmd-cli with the base Gemma 4 GGUF + mmproj multimodal projector.

Public API:
  transcribe(text, hint_lang)       -> TranscriptionResult
  transcribe_audio(wav_path)        -> str  (speech → English text)
  _generate_text(prompt)            -> str
  _generate_chat(messages)          -> str
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

# Restrict to RTX 4090 before llama_cpp initialises (ggml_cuda_init reads this).
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")

from llama_cpp import Llama

if TYPE_CHECKING:
    from models.audio_transcriber import GemmaAudioTranscriber

_GGUF_REPO = "OminousDude/voicebridge-gemma4"
_GGUF_FILENAME = "voicebridge-finetuned-q4km.gguf"

_TRANSCRIBE_PROMPT = (
    "Given the following patient statement, respond with JSON only:\n"
    "{\n"
    '  "original_text": "<verbatim patient text>",\n'
    '  "english_text": "<accurate English translation>",\n'
    '  "detected_language": "<ISO 639-1 code>"\n'
    "}"
)


@dataclass
class TranscriptionResult:
    original_text: str
    english_text: str
    detected_language: str
    duration_s: float


def _extract_json(raw: str) -> dict:
    """
    Extract the first {...} block from a string that may contain
    extra tokens before/after the JSON object.
    Raises ValueError if no valid JSON object is found.
    """
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in model output: {raw!r}")
    return json.loads(raw[start : end + 1])


def _resolve_gguf_path(model_path: str) -> str:
    """
    Resolve the GGUF file path.

    Priority:
      1. Env var VOICEBRIDGE_GGUF_PATH if set and file exists.
      2. If model_path itself is a .gguf file that exists, use it.
      3. If model_path is a directory, look for *.gguf inside it.
      4. Fall back to downloading from HuggingFace Hub.
    """
    import os
    env_path = os.environ.get("VOICEBRIDGE_GGUF_PATH")
    if env_path and Path(env_path).is_file():
        return env_path

    p = Path(model_path)

    if p.is_file() and p.suffix == ".gguf":
        return str(p)

    if p.is_dir():
        candidates = list(p.glob("*.gguf"))
        if candidates:
            return str(candidates[0])

    # Download from Hub — cached under ~/.cache/huggingface/hub
    print(f"GGUF not found at {model_path!r}. Downloading from {_GGUF_REPO} ...")
    from huggingface_hub import hf_hub_download
    local = hf_hub_download(repo_id=_GGUF_REPO, filename=_GGUF_FILENAME)
    print(f"Downloaded GGUF to {local}")
    return local


class GemmaTranscriber:
    """
    Wraps the quantized Gemma 4 GGUF via llama-cpp-python for:
      - transcribe()      — pre-transcribed text → TranscriptionResult
      - _generate_text()  — text prompt → str  (used by TriageClassifier)
      - _generate_chat()  — message list → str (used by interactive mode)
    """

    def __init__(self, model_path: str) -> None:
        gguf_path = _resolve_gguf_path(model_path)
        print(f"Loading GGUF from {gguf_path} on RTX 4090 (CUDA device 1)")
        self._llm = Llama(
            model_path=gguf_path,
            n_gpu_layers=-1,
            n_ctx=4096,
            main_gpu=0,  # only RTX 4090 visible (CUDA_VISIBLE_DEVICES=1)
            use_mmap=False,  # required for CUDA DMA in WSL2
            verbose=True,
        )
        self._audio_tx: GemmaAudioTranscriber | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transcribe_audio(self, wav_path: str) -> str:
        """
        Transcribe a 16 kHz mono WAV file to English text using Gemma 4
        native audio tower (base model + mmproj multimodal projector).

        Lazily initialises GemmaAudioTranscriber on first call.
        Requires llama-mtmd-cli to be built — see scripts/build_llama_mtmd.ps1.

        Args:
            wav_path: Path to a 16 kHz mono WAV file.

        Returns:
            Transcribed English text string.
        """
        if self._audio_tx is None:
            from models.audio_transcriber import GemmaAudioTranscriber
            # GPU 1 = RTX 4090 (idle). GPU 0 = RTX 5090 (hosting llama-server, full).
            self._audio_tx = GemmaAudioTranscriber(gpu_device=1)
        return self._audio_tx.transcribe_audio(wav_path)

    def transcribe(self, text: str, hint_lang: str = "") -> TranscriptionResult:
        """
        Wrap pre-transcribed patient text into a structured TranscriptionResult.

        The GGUF stores the text decoder only — audio encoding is not available.
        Pass text that has already been transcribed (e.g. via Whisper).

        Args:
            text:      Pre-transcribed patient statement.
            hint_lang: Optional ISO 639-1 language hint (e.g. 'sw').

        Returns:
            TranscriptionResult with original + English text.
        """
        prompt = (
            f"The speaker is using {hint_lang}.\n{_TRANSCRIBE_PROMPT}\n\nPatient: {text}"
            if hint_lang
            else f"{_TRANSCRIBE_PROMPT}\n\nPatient: {text}"
        )
        messages = [{"role": "user", "content": prompt}]
        raw = self._generate_chat(messages, max_tokens=256)
        try:
            data = _extract_json(raw)
        except (ValueError, json.JSONDecodeError):
            data = {
                "original_text": text,
                "english_text": text,
                "detected_language": hint_lang or "en",
            }
        return TranscriptionResult(
            original_text=data.get("original_text", text),
            english_text=data.get("english_text", text),
            detected_language=data.get("detected_language", hint_lang or "en"),
            duration_s=0.0,
        )

    def _generate_chat(self, messages: list[dict], max_tokens: int = 512) -> str:
        """
        Multi-turn generation with full message history.
        messages: list of {role, content} dicts (system, user, assistant).
        """
        result = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,
            top_p=0.9,
            repeat_penalty=1.3,
        )
        return result["choices"][0]["message"]["content"].strip()

    def _generate_text(self, prompt: str, max_tokens: int = 1024) -> str:
        """Text-only generation — used by TriageClassifier."""
        result = self._llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
        )
        return result["choices"][0]["message"]["content"].strip()
