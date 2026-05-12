"""
Language identification module for VoiceBridge.

Two detection strategies:
  - Audio-based  : facebook/mms-lid-256 (256 languages, ~190 MB)
  - Text-based   : langdetect (fallback when audio LID fails)

The MMS pipeline is loaded lazily on first call so that importing this
module never blocks startup.
"""

from __future__ import annotations

import numpy as np
import langdetect
from transformers import pipeline

SUPPORTED_LANGS: dict[str, str] = {
    "sw": "Swahili",
    "ha": "Hausa",
    "yo": "Yoruba",
    "ig": "Igbo",
    "am": "Amharic",
    "om": "Oromo",
    "so": "Somali",
    "rw": "Kinyarwanda",
    "ln": "Lingala",
    "mg": "Malagasy",
    "hi": "Hindi",
    "bn": "Bengali",
    "ur": "Urdu",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "si": "Sinhala",
    "tl": "Tagalog",
    "id": "Indonesian",
    "ms": "Malay",
    "my": "Burmese",
    "km": "Khmer",
    "lo": "Lao",
    "ar": "Arabic",
    "fa": "Farsi",
    "ps": "Pashto",
    "ku": "Kurdish",
    "zh": "Chinese",
    "es": "Spanish",
    "pt": "Portuguese",
    "fr": "French",
    "en": "English",
    "ru": "Russian",
    "uk": "Ukrainian",
    "tr": "Turkish",
    "uz": "Uzbek",
    "kk": "Kazakh",
}

_lid_pipe = None


def _get_lid_pipe():
    """Load the MMS-LID-256 pipeline on first call (CPU, laptop-safe)."""
    global _lid_pipe
    if _lid_pipe is None:
        _lid_pipe = pipeline(
            "audio-classification",
            model="facebook/mms-lid-256",
            device=-1,
        )
    return _lid_pipe


def pre_load_lid() -> None:
    """Pre-load the language ID model so the first request is not blocked."""
    global _lid_pipe
    if _lid_pipe is None:
        print("Pre-loading language ID model (facebook/mms-lid-256)...")
        _lid_pipe = pipeline(
            "audio-classification",
            model="facebook/mms-lid-256",
            device=-1,
        )
        print("Language ID model loaded.")


def detect_language_from_audio(audio: np.ndarray, sampling_rate: int = 16000) -> str:
    """
    Identify the spoken language in a 16 kHz float32 audio array.

    Returns the best-match ISO 639-1 code (2 chars).
    Falls back to 'en' if the model output cannot be mapped.
    """
    pipe = _get_lid_pipe()
    result = pipe({"array": audio, "sampling_rate": sampling_rate})
    label: str = result[0]["label"]
    return label[:2]


def detect_language_from_text(text: str) -> str:
    """
    Identify the language of a text string using langdetect.

    Returns the ISO 639-1 code, or 'en' on any failure.
    """
    try:
        return langdetect.detect(text)
    except Exception:
        return "en"


def is_supported(lang_code: str) -> bool:
    """Return True if the 2-char ISO code is in the supported language table."""
    return lang_code in SUPPORTED_LANGS


def language_name(lang_code: str) -> str:
    """Return the human-readable name for a supported language code."""
    return SUPPORTED_LANGS.get(lang_code, f"Unknown ({lang_code})")
