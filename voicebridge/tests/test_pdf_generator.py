"""
Unit tests for pipeline/pdf_generator.py.

ReportLab always compresses the content stream (ASCII85 + FlateDecode),
so raw-byte text searches are not reliable. Tests use:
  - Structural checks (PDF magic, minimum size, valid bytes)
  - Size-delta checks (more content → larger file)
  - Direct helper tests (LEVEL_COLORS, LEVEL_WAIT coverage)
  - TriageOutput construction (validates the data that feeds the PDF)
"""

import pytest

from pipeline.pdf_generator import (
    LEVEL_COLORS,
    LEVEL_WAIT,
    generate_triage_pdf,
)
from pipeline.triage import TriageLevel, TriageOutput

_REAL_LEVELS = [
    TriageLevel.RED,
    TriageLevel.ORANGE,
    TriageLevel.YELLOW,
    TriageLevel.GREEN,
    TriageLevel.BLUE,
]


def _make_result(level: TriageLevel, **overrides) -> TriageOutput:
    defaults = {
        "triage_level": level,
        "primary_complaint": "Test complaint",
        "reported_symptoms": ["fever", "cough"],
        "vital_signs_reported": {"rr": "22/min", "hr": "88 bpm"},
        "duration_of_symptoms": "2 days",
        "relevant_history": "None",
        "red_flag_indicators": [],
        "recommended_action": "Observe and reassess in 1 hour",
        "referral_needed": False,
        "confidence_score": 0.85,
        "source_language": "en",
        "raw_transcript": "Patient reports fever and cough for two days.",
    }
    defaults.update(overrides)
    return TriageOutput(**defaults)


# ---------------------------------------------------------------------------
# Colour / wait-time table completeness
# ---------------------------------------------------------------------------

class TestColorTables:
    def test_all_levels_have_color(self):
        for level in _REAL_LEVELS:
            assert level in LEVEL_COLORS, f"Missing colour for {level}"

    def test_all_levels_have_wait_text(self):
        for level in _REAL_LEVELS:
            assert level in LEVEL_WAIT, f"Missing wait text for {level}"

    def test_red_is_different_from_green(self):
        assert LEVEL_COLORS[TriageLevel.RED] != LEVEL_COLORS[TriageLevel.GREEN]


# ---------------------------------------------------------------------------
# PDF structure — valid bytes for every level
# ---------------------------------------------------------------------------

class TestGenerateTriagePdf:

    @pytest.mark.parametrize("level", _REAL_LEVELS)
    def test_returns_bytes_for_every_level(self, level):
        pdf = generate_triage_pdf(_make_result(level))
        assert isinstance(pdf, bytes)
        assert len(pdf) > 500

    @pytest.mark.parametrize("level", _REAL_LEVELS)
    def test_starts_with_pdf_magic(self, level):
        pdf = generate_triage_pdf(_make_result(level))
        assert pdf[:4] == b"%PDF", f"Not a valid PDF for level {level}"

    @pytest.mark.parametrize("level", _REAL_LEVELS)
    def test_ends_with_eof_marker(self, level):
        pdf = generate_triage_pdf(_make_result(level))
        assert b"%%EOF" in pdf[-64:]

    def test_default_facility_name(self):
        """Smoke test — default facility should not raise."""
        pdf = generate_triage_pdf(_make_result(TriageLevel.ORANGE))
        assert pdf[:4] == b"%PDF"

    def test_custom_facility_accepted(self):
        """Custom facility string should not raise."""
        pdf = generate_triage_pdf(
            _make_result(TriageLevel.ORANGE),
            facility="Kenyatta National Hospital",
        )
        assert pdf[:4] == b"%PDF"

    # ---- Content size delta tests ----------------------------------------
    # More data → bigger compressed stream.  Not guaranteed by spec but
    # holds in practice for the content volumes used here.

    def test_more_red_flags_increases_pdf_size(self):
        base = generate_triage_pdf(_make_result(TriageLevel.RED,
                                                red_flag_indicators=[]))
        with_flags = generate_triage_pdf(_make_result(
            TriageLevel.RED,
            red_flag_indicators=["active seizure", "GCS < 9",
                                  "RR > 29", "SpO2 < 90%"],
        ))
        assert len(with_flags) > len(base)

    def test_referral_true_accepted(self):
        """referral_needed=True should not raise."""
        pdf = generate_triage_pdf(
            _make_result(TriageLevel.RED, referral_needed=True)
        )
        assert pdf[:4] == b"%PDF"

    def test_confidence_boundary_values(self):
        for score in (0.0, 0.5, 1.0):
            pdf = generate_triage_pdf(_make_result(TriageLevel.GREEN,
                                                   confidence_score=score))
            assert pdf[:4] == b"%PDF"

    # ---- Edge cases -------------------------------------------------------

    def test_empty_vitals(self):
        pdf = generate_triage_pdf(
            _make_result(TriageLevel.GREEN, vital_signs_reported={})
        )
        assert pdf[:4] == b"%PDF"

    def test_empty_red_flags_does_not_raise(self):
        pdf = generate_triage_pdf(
            _make_result(TriageLevel.GREEN, red_flag_indicators=[])
        )
        assert pdf[:4] == b"%PDF"

    def test_empty_symptoms_does_not_raise(self):
        pdf = generate_triage_pdf(
            _make_result(TriageLevel.YELLOW, reported_symptoms=[])
        )
        assert pdf[:4] == b"%PDF"
