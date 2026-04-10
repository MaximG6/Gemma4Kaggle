"""
Integration tests for api/main.py.

The full model pipeline (transcriber + classifier + language-id) is
mocked so tests run fast with no downloaded weights.
All SQLite operations run against an in-memory database via StaticPool.
"""

import io
import json
import os
import struct
import uuid
import wave
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Must be set BEFORE importing app modules so db.py picks it up at import time.
os.environ["VOICEBRIDGE_DB_URL"] = "sqlite:///:memory:"

from api.main import app  # noqa: E402
from pipeline.triage import TriageLevel, TriageOutput  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """TestClient that runs the lifespan (calls init_db) for each test."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wav(num_samples: int = 16000, sample_rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{num_samples}h", *([0] * num_samples)))
    return buf.getvalue()


_TRIAGE_DICT = {
    "triage_level": "orange",
    "primary_complaint": "High fever with altered consciousness",
    "reported_symptoms": ["fever", "altered consciousness"],
    "vital_signs_reported": {"temp": "39.8 C", "hr": "118 bpm"},
    "duration_of_symptoms": "6 hours",
    "relevant_history": "None",
    "red_flag_indicators": ["HR > 100"],
    "recommended_action": "IV access, fluids, urgent physician review",
    "referral_needed": True,
    "confidence_score": 0.91,
    "source_language": "sw",
    "raw_transcript": "Patient has had a high fever for 6 hours.",
}


def _make_triage_output() -> TriageOutput:
    return TriageOutput(**_TRIAGE_DICT)


def _patch_pipeline(triage_output: TriageOutput):
    """Return two context managers that patch the full model pipeline."""
    from models.transcription import TranscriptionResult

    mock_tx = MagicMock()
    mock_tx.transcribe.return_value = TranscriptionResult(
        original_text="Mgonjwa ana homa.",
        english_text="Patient has had a high fever for 6 hours.",
        detected_language="sw",
        duration_s=1.0,
    )

    mock_clf = MagicMock()
    mock_clf.classify.return_value = triage_output

    return (
        patch("api.main._get_models", return_value=(mock_tx, mock_clf)),
        patch("api.main.detect_language_from_audio", return_value="sw"),
    )


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /intake
# ---------------------------------------------------------------------------

class TestIntake:
    def test_intake_returns_triage_json(self, client):
        triage = _make_triage_output()
        p1, p2 = _patch_pipeline(triage)
        with p1, p2:
            resp = client.post(
                "/intake",
                files={"file": ("test.wav", _make_wav(), "audio/wav")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "record_id" in data
        assert data["triage"]["triage_level"] == "orange"
        assert data["triage"]["referral_needed"] is True

    def test_intake_empty_file_returns_400(self, client):
        p1, p2 = _patch_pipeline(_make_triage_output())
        with p1, p2:
            resp = client.post(
                "/intake",
                files={"file": ("empty.wav", b"", "audio/wav")},
            )
        assert resp.status_code == 400

    def test_intake_record_id_is_uuid(self, client):
        triage = _make_triage_output()
        p1, p2 = _patch_pipeline(triage)
        with p1, p2:
            resp = client.post(
                "/intake",
                files={"file": ("t.wav", _make_wav(), "audio/wav")},
            )
        record_id = resp.json()["record_id"]
        uuid.UUID(record_id)  # raises if not a valid UUID

    def test_intake_all_triage_fields_present(self, client):
        triage = _make_triage_output()
        p1, p2 = _patch_pipeline(triage)
        with p1, p2:
            resp = client.post(
                "/intake",
                files={"file": ("t.wav", _make_wav(), "audio/wav")},
            )
        t = resp.json()["triage"]
        for field in ("triage_level", "primary_complaint", "reported_symptoms",
                      "vital_signs_reported", "recommended_action",
                      "referral_needed", "confidence_score", "source_language"):
            assert field in t, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# /intake/pdf
# ---------------------------------------------------------------------------

class TestIntakePdf:
    def test_returns_pdf_bytes(self, client):
        triage = _make_triage_output()
        p1, p2 = _patch_pipeline(triage)
        with p1, p2:
            resp = client.post(
                "/intake/pdf",
                files={"file": ("t.wav", _make_wav(), "audio/wav")},
            )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_pdf_content_disposition(self, client):
        triage = _make_triage_output()
        p1, p2 = _patch_pipeline(triage)
        with p1, p2:
            resp = client.post(
                "/intake/pdf",
                files={"file": ("t.wav", _make_wav(), "audio/wav")},
            )
        assert "triage.pdf" in resp.headers["content-disposition"]


# ---------------------------------------------------------------------------
# /records
# ---------------------------------------------------------------------------

class TestRecords:
    def test_records_returns_list(self, client):
        resp = client.get("/records")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_records_bad_limit_zero(self, client):
        resp = client.get("/records?limit=0")
        assert resp.status_code == 400

    def test_records_limit_too_large(self, client):
        resp = client.get("/records?limit=501")
        assert resp.status_code == 400

    def test_record_not_found(self, client):
        resp = client.get("/records/nonexistent-id")
        assert resp.status_code == 404
