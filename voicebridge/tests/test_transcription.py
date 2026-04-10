"""
Unit tests for models/transcription.py.

The Gemma model is mocked so tests run without downloaded weights.
"""

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from models.transcription import GemmaTranscriber, TranscriptionResult, _extract_json


# ---------------------------------------------------------------------------
# _extract_json helper
# ---------------------------------------------------------------------------

class TestExtractJson:
    def test_clean_json(self):
        raw = '{"a": 1, "b": "hello"}'
        assert _extract_json(raw) == {"a": 1, "b": "hello"}

    def test_json_with_prefix_text(self):
        raw = 'Here is the output: {"key": "value"} done.'
        assert _extract_json(raw) == {"key": "value"}

    def test_nested_json(self):
        raw = '{"outer": {"inner": 42}}'
        result = _extract_json(raw)
        assert result["outer"]["inner"] == 42

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON object"):
            _extract_json("no braces here at all")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            _extract_json("")


# ---------------------------------------------------------------------------
# GemmaTranscriber (model mocked)
# ---------------------------------------------------------------------------

def _make_mock_transcriber():
    """Return a GemmaTranscriber with processor and model fully mocked."""
    with patch("models.transcription.AutoProcessor") as MockProc, \
         patch("models.transcription.Gemma4ForConditionalGeneration") as MockModel:

        mock_proc  = MagicMock()
        mock_model = MagicMock()

        MockProc.from_pretrained.return_value  = mock_proc
        MockModel.from_pretrained.return_value = mock_model

        tx = GemmaTranscriber("/fake/model/path")
        return tx, mock_proc, mock_model


class TestGemmaTranscriber:

    def _silence(self, seconds: float = 1.0) -> np.ndarray:
        return np.zeros(int(16000 * seconds), dtype=np.float32)

    def test_transcribe_returns_result(self):
        tx, mock_proc, mock_model = _make_mock_transcriber()

        json_output = json.dumps({
            "original_text": "Mgonjwa ana homa kali.",
            "english_text":  "The patient has severe fever.",
            "detected_language": "sw",
        })
        mock_proc.decode.return_value = json_output
        mock_model.generate.return_value = MagicMock()

        result = tx.transcribe(self._silence(), hint_lang="sw")

        assert isinstance(result, TranscriptionResult)
        assert result.original_text == "Mgonjwa ana homa kali."
        assert result.english_text  == "The patient has severe fever."
        assert result.detected_language == "sw"
        assert abs(result.duration_s - 1.0) < 0.05

    def test_transcribe_falls_back_to_hint_lang(self):
        tx, mock_proc, mock_model = _make_mock_transcriber()

        # No detected_language in model output → should use hint_lang
        json_output = json.dumps({
            "original_text": "text",
            "english_text":  "text",
        })
        mock_proc.decode.return_value = json_output
        mock_model.generate.return_value = MagicMock()

        result = tx.transcribe(self._silence(), hint_lang="ha")
        assert result.detected_language == "ha"

    def test_transcribe_no_hint_lang(self):
        tx, mock_proc, mock_model = _make_mock_transcriber()

        json_output = json.dumps({
            "original_text": "hello",
            "english_text":  "hello",
            "detected_language": "en",
        })
        mock_proc.decode.return_value = json_output
        mock_model.generate.return_value = MagicMock()

        result = tx.transcribe(self._silence())
        assert result.detected_language == "en"

    def test_transcribe_duration_correct(self):
        tx, mock_proc, mock_model = _make_mock_transcriber()

        mock_proc.decode.return_value = json.dumps({
            "original_text": "x", "english_text": "x", "detected_language": "en"
        })
        mock_model.generate.return_value = MagicMock()

        audio = self._silence(3.0)
        result = tx.transcribe(audio)
        assert abs(result.duration_s - 3.0) < 0.05

    def test_generate_text_strips_prompt(self):
        tx, mock_proc, _ = _make_mock_transcriber()

        prompt = "Classify this:"
        mock_proc.decode.return_value = prompt + " the answer"
        tx.model.generate = MagicMock(return_value=MagicMock())

        output = tx._generate_text(prompt)
        assert output == "the answer"

    def test_generate_text_no_prompt_prefix(self):
        tx, mock_proc, _ = _make_mock_transcriber()

        mock_proc.decode.return_value = '{"result": "ok"}'
        tx.model.generate = MagicMock(return_value=MagicMock())

        output = tx._generate_text("some prompt that is not in output")
        assert output == '{"result": "ok"}'
