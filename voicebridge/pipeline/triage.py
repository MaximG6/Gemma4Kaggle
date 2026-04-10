"""
SATS-aligned triage classifier with Pydantic schema (Task 2.2).

TriageOutput is the canonical structured result for a patient intake.
Every field maps to a real clinical concept validated against:
  - South African Triage Scale (SATS 2023)
  - WHO Emergency Triage Assessment and Treatment (ETAT) guidelines

TriageClassifier drives Gemma to produce a TriageOutput from any
English-language intake transcript via structured JSON prompting.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from models.transcription import GemmaTranscriber


# ---------------------------------------------------------------------------
# SATS 2023 triage levels
# ---------------------------------------------------------------------------

# Severity order for comparison — kept outside the enum so it is not
# interpreted as an enum member by Python's Enum metaclass.
_LEVEL_ORDER = ["blue", "green", "yellow", "orange", "red"]


class TriageLevel(str, Enum):
    RED = "red"       # Immediate — life-threatening, see within seconds
    ORANGE = "orange" # Very urgent — see within 10 minutes
    YELLOW = "yellow" # Urgent — see within 60 minutes
    GREEN = "green"   # Routine — see within 4 hours
    BLUE = "blue"     # Deceased or expectant (no survivable treatment available)

    def __lt__(self, other: "TriageLevel") -> bool:
        return _LEVEL_ORDER.index(self.value) < _LEVEL_ORDER.index(other.value)

    def __le__(self, other: "TriageLevel") -> bool:
        return _LEVEL_ORDER.index(self.value) <= _LEVEL_ORDER.index(other.value)

    def __gt__(self, other: "TriageLevel") -> bool:
        return _LEVEL_ORDER.index(self.value) > _LEVEL_ORDER.index(other.value)

    def __ge__(self, other: "TriageLevel") -> bool:
        return _LEVEL_ORDER.index(self.value) >= _LEVEL_ORDER.index(other.value)


# ---------------------------------------------------------------------------
# Triage output schema
# ---------------------------------------------------------------------------

class TriageOutput(BaseModel):
    """
    Structured triage result aligned with SATS 2023 criteria.

    All fields are required; the model must populate every one.
    """

    triage_level: TriageLevel
    """SATS 2023 colour code — red/orange/yellow/green/blue."""

    primary_complaint: str = Field(max_length=200)
    """Chief presenting complaint in one sentence."""

    reported_symptoms: list[str] = Field(default_factory=list)
    """Up to 10 discrete symptoms as reported by the nurse."""

    vital_signs_reported: dict[str, str]
    """Key–value pairs of any vitals mentioned (e.g. {'rr': '32/min'})."""

    duration_of_symptoms: str
    """Free-text duration as reported (e.g. '2 hours', 'since yesterday')."""

    relevant_history: str = Field(max_length=300)
    """Pertinent medical history mentioned in the intake."""

    red_flag_indicators: list[str]
    """Explicit SATS 2023 / WHO ETAT red-flag criteria matched in this case."""

    recommended_action: str
    """Immediate clinical action the health worker should take."""

    referral_needed: bool
    """True if the patient requires transfer to a higher-level facility."""

    confidence_score: float = Field(ge=0.0, le=1.0)
    """Model's self-reported confidence (0–1). Used for safety auditing."""

    source_language: str
    """ISO 639-1 code of the original intake language."""

    raw_transcript: str
    """The English transcript that was classified."""


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a clinical triage assistant trained on SATS 2023 and WHO ETAT guidelines.

SATS RED criteria (any one → RED):
  • Airway: completely obstructed
  • Respiratory rate < 10 or > 29 per minute
  • SpO2 < 90% on room air
  • Heart rate < 40 or > 150 bpm
  • GCS < 9
  • AVPU = P (responds to Pain) or U (Unresponsive)
  • Major uncontrolled haemorrhage
  • Active seizure / convulsions
  • Temperature > 41 °C
  • Blood glucose < 3 mmol/L with altered consciousness

Be conservative: when uncertain, escalate urgency rather than downgrade.
Do NOT add commentary. Respond ONLY with a single valid JSON object matching:

{schema}

Nurse intake transcript:
{transcript}"""


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class TriageClassifier:
    """
    Classifies an English intake transcript into a TriageOutput using
    structured JSON prompting via GemmaTranscriber._generate_text().
    """

    def __init__(self, transcriber: "GemmaTranscriber") -> None:
        self._tx = transcriber

    def classify(self, transcript: str, source_lang: str = "en") -> TriageOutput:
        """
        Args:
            transcript:  English-language intake text.
            source_lang: ISO 639-1 code of the original spoken language.

        Returns:
            Validated TriageOutput instance.

        Raises:
            ValueError: If the model returns unparseable output.
            pydantic.ValidationError: If required fields are missing/invalid.
        """
        schema = json.dumps(TriageOutput.model_json_schema(), indent=2)
        prompt = _SYSTEM_PROMPT.format(schema=schema, transcript=transcript)
        raw = self._tx._generate_text(prompt, max_tokens=1024)

        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"No JSON object in triage model output: {raw!r}")

        data = json.loads(raw[start : end + 1])
        data["source_language"] = source_lang
        data["raw_transcript"] = transcript
        return TriageOutput(**data)
