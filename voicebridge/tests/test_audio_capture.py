"""
Unit tests for api/audio_capture.py — resample_to_16k and upload endpoint.
"""

import io
import struct
import wave

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.audio_capture import resample_to_16k


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _make_wav(num_samples: int, sample_rate: int) -> bytes:
    """Generate a minimal silent WAV file in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{num_samples}h", *([0] * num_samples)))
    return buf.getvalue()


class TestResampleTo16k:
    def test_already_16k_unchanged_length(self):
        wav = _make_wav(16000, 16000)
        arr = resample_to_16k(wav)
        assert arr.dtype == np.float32
        assert abs(len(arr) - 16000) <= 10

    def test_8k_upsampled_to_16k(self):
        wav = _make_wav(8000, 8000)
        arr = resample_to_16k(wav)
        assert abs(len(arr) - 16000) <= 50

    def test_44100_downsampled_to_16k(self):
        wav = _make_wav(44100, 44100)
        arr = resample_to_16k(wav)
        assert abs(len(arr) - 16000) <= 50

    def test_returns_float32(self):
        wav = _make_wav(16000, 16000)
        arr = resample_to_16k(wav)
        assert arr.dtype == np.float32


class TestUploadEndpoint:
    def test_upload_returns_duration(self, client):
        wav = _make_wav(16000, 16000)  # 1 second
        resp = client.post(
            "/audio/upload",
            files={"file": ("test.wav", wav, "audio/wav")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert abs(data["duration_s"] - 1.0) < 0.1
        assert data["samples"] > 0
        assert data["filename"] == "test.wav"

    def test_upload_2_seconds(self, client):
        wav = _make_wav(32000, 16000)  # 2 seconds
        resp = client.post(
            "/audio/upload",
            files={"file": ("two_sec.wav", wav, "audio/wav")},
        )
        assert resp.status_code == 200
        assert abs(resp.json()["duration_s"] - 2.0) < 0.1
