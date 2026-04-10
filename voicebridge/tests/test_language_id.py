"""
Unit tests for models/language_id.py.

MMS-LID model calls are mocked so these run without any download.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from models.language_id import (
    SUPPORTED_LANGS,
    detect_language_from_audio,
    detect_language_from_text,
    is_supported,
    language_name,
)


class TestSupportedLangsTable:
    def test_has_40_entries(self):
        assert len(SUPPORTED_LANGS) >= 40

    def test_english_present(self):
        assert "en" in SUPPORTED_LANGS

    def test_swahili_present(self):
        assert "sw" in SUPPORTED_LANGS

    def test_all_keys_are_2_chars(self):
        for code in SUPPORTED_LANGS:
            assert len(code) == 2, f"Bad code: {code!r}"


class TestIsSupported:
    def test_known_language(self):
        assert is_supported("sw") is True

    def test_unknown_language(self):
        assert is_supported("xx") is False


class TestLanguageName:
    def test_known_returns_name(self):
        assert language_name("en") == "English"

    def test_unknown_returns_fallback(self):
        result = language_name("xx")
        assert "xx" in result


class TestDetectFromText:
    def test_english_text(self):
        code = detect_language_from_text("The patient presents with fever and cough.")
        assert code == "en"

    def test_empty_string_returns_en(self):
        code = detect_language_from_text("")
        assert code == "en"

    def test_exception_returns_en(self):
        with patch("models.language_id.langdetect.detect", side_effect=Exception("fail")):
            assert detect_language_from_text("anything") == "en"


class TestDetectFromAudio:
    def _make_silence(self, seconds: float = 1.0) -> np.ndarray:
        return np.zeros(int(16000 * seconds), dtype=np.float32)

    def test_returns_2char_string(self):
        mock_pipe = MagicMock(return_value=[{"label": "eng", "score": 0.99}])
        with patch("models.language_id._get_lid_pipe", return_value=mock_pipe):
            result = detect_language_from_audio(self._make_silence())
        assert isinstance(result, str)
        assert len(result) == 2

    def test_swahili_label_mapped(self):
        mock_pipe = MagicMock(return_value=[{"label": "swh", "score": 0.95}])
        with patch("models.language_id._get_lid_pipe", return_value=mock_pipe):
            result = detect_language_from_audio(self._make_silence())
        assert result == "sw"

    def test_accepts_custom_sampling_rate(self):
        mock_pipe = MagicMock(return_value=[{"label": "fra", "score": 0.80}])
        with patch("models.language_id._get_lid_pipe", return_value=mock_pipe):
            audio = np.zeros(8000, dtype=np.float32)
            result = detect_language_from_audio(audio, sampling_rate=8000)
        assert result == "fr"
