"""
Unit tests for pipeline/triage.py.

TriageClassifier._generate_text is mocked so no model is needed.
"""

import json
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from pipeline.triage import TriageClassifier, TriageLevel, TriageOutput


# ---------------------------------------------------------------------------
# TriageLevel ordering
# ---------------------------------------------------------------------------

class TestTriageLevelOrdering:
    def test_red_greater_than_green(self):
        assert TriageLevel.RED > TriageLevel.GREEN

    def test_orange_greater_than_yellow(self):
        assert TriageLevel.ORANGE > TriageLevel.YELLOW

    def test_blue_least(self):
        for level in [TriageLevel.GREEN, TriageLevel.YELLOW, TriageLevel.ORANGE, TriageLevel.RED]:
            assert TriageLevel.BLUE < level

    def test_equality(self):
        assert TriageLevel.RED >= TriageLevel.RED
        assert TriageLevel.RED <= TriageLevel.RED


# ---------------------------------------------------------------------------
# TriageOutput schema
# ---------------------------------------------------------------------------

_VALID_DATA = {
    "triage_level": "red",
    "primary_complaint": "Active seizure",
    "reported_symptoms": ["convulsions", "unresponsive"],
    "vital_signs_reported": {"gcs": "3", "rr": "8"},
    "duration_of_symptoms": "5 minutes",
    "relevant_history": "No known epilepsy",
    "red_flag_indicators": ["active seizure", "GCS < 9"],
    "recommended_action": "Protect airway, administer diazepam, urgent transfer",
    "referral_needed": True,
    "confidence_score": 0.97,
    "source_language": "sw",
    "raw_transcript": "Patient is convulsing.",
}


class TestTriageOutput:
    def test_valid_construction(self):
        t = TriageOutput(**_VALID_DATA)
        assert t.triage_level == TriageLevel.RED
        assert t.referral_needed is True

    def test_confidence_out_of_range_raises(self):
        data = {**_VALID_DATA, "confidence_score": 1.5}
        with pytest.raises(ValidationError):
            TriageOutput(**data)

    def test_confidence_lower_bound(self):
        data = {**_VALID_DATA, "confidence_score": -0.1}
        with pytest.raises(ValidationError):
            TriageOutput(**data)

    def test_invalid_triage_level_raises(self):
        data = {**_VALID_DATA, "triage_level": "purple"}
        with pytest.raises(ValidationError):
            TriageOutput(**data)

    def test_primary_complaint_max_length(self):
        data = {**_VALID_DATA, "primary_complaint": "x" * 201}
        with pytest.raises(ValidationError):
            TriageOutput(**data)

    def test_relevant_history_max_length(self):
        data = {**_VALID_DATA, "relevant_history": "x" * 301}
        with pytest.raises(ValidationError):
            TriageOutput(**data)

    def test_model_dump_roundtrip(self):
        t = TriageOutput(**_VALID_DATA)
        dumped = t.model_dump()
        assert dumped["triage_level"] == "red"
        assert dumped["confidence_score"] == 0.97


# ---------------------------------------------------------------------------
# TriageClassifier
# ---------------------------------------------------------------------------

def _make_mock_transcriber(json_response: str) -> MagicMock:
    mock_tx = MagicMock()
    mock_tx._generate_text.return_value = json_response
    return mock_tx


class TestTriageClassifier:

    def _classifier(self, json_resp: str) -> TriageClassifier:
        return TriageClassifier(_make_mock_transcriber(json_resp))

    def _valid_json(self, overrides: dict = {}) -> str:
        data = {**_VALID_DATA}
        del data["source_language"]  # classifier injects this
        del data["raw_transcript"]   # classifier injects this
        data.update(overrides)
        return json.dumps(data)

    def test_classify_returns_triage_output(self):
        clf = self._classifier(self._valid_json())
        result = clf.classify("Patient is convulsing.", source_lang="sw")
        assert isinstance(result, TriageOutput)
        assert result.triage_level == TriageLevel.RED

    def test_classifier_injects_source_language(self):
        clf = self._classifier(self._valid_json())
        result = clf.classify("text", source_lang="tl")
        assert result.source_language == "tl"

    def test_classifier_injects_raw_transcript(self):
        clf = self._classifier(self._valid_json())
        result = clf.classify("some intake text", source_lang="en")
        assert result.raw_transcript == "some intake text"

    def test_json_with_surrounding_text(self):
        """Model output may have text before/after the JSON block."""
        prefix = "Here is my assessment:\n"
        suffix = "\nEnd of response."
        clf = self._classifier(prefix + self._valid_json() + suffix)
        result = clf.classify("text", source_lang="en")
        assert isinstance(result, TriageOutput)

    def test_no_json_raises_value_error(self):
        clf = self._classifier("I cannot provide a triage assessment.")
        with pytest.raises(ValueError, match="No JSON object"):
            clf.classify("text", source_lang="en")

    def test_green_level(self):
        data = {**_VALID_DATA}
        del data["source_language"]
        del data["raw_transcript"]
        data["triage_level"] = "green"
        data["red_flag_indicators"] = []
        data["referral_needed"] = False
        clf = self._classifier(json.dumps(data))
        result = clf.classify("Mild headache for two days.", source_lang="en")
        assert result.triage_level == TriageLevel.GREEN
