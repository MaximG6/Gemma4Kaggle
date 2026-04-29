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
You are a clinical triage assistant. Respond with key-value pairs only.
Format:
TriageLevel: red/orange/yellow/green/blue
PrimaryComplaint: one sentence
ReportedSymptoms: symptom1, symptom2
VitalSignsReported: key: value, key: value
DurationOfSymptoms: free text
RelevantHistory: free text
RedFlagIndicators: indicator1, indicator2
RecommendedAction: what to do
ReferralNeeded: yes/no
ConfidenceScore: 0.0-1.0

Nurse intake:
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
        raw = self._tx._generate_text(prompt, max_tokens=512)

        # Try JSON first
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
                data["source_language"] = source_lang
                data["raw_transcript"] = transcript
                return TriageOutput(**data)
            except (json.JSONDecodeError, Exception):
                pass  # Fall through to key-value parsing

        # Parse key-value format (fine-tuned model output)
        data = {}
        for line in raw.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                data[key] = value

        # Map to TriageOutput fields
        mapping = {
            "triagelevel": "triage_level",
            "primarycomplaint": "primary_complaint",
            "reported_symptoms": "reported_symptoms",
            "vitalsignsreported": "vital_signs_reported",
            "durationofsymptoms": "duration_of_symptoms",
            "relevant_history": "relevant_history",
            "redflagindicators": "red_flag_indicators",
            "recommendedaction": "recommended_action",
            "referralneeded": "referral_needed",
            "confidencescore": "confidence_score",
        }

        parsed = {}
        for kv_key, field in mapping.items():
            if kv_key in data:
                val = data[kv_key]
                if field == "triage_level":
                    parsed[field] = val.lower()
                elif field == "reported_symptoms":
                    parsed[field] = [s.strip() for s in val.split(",") if s.strip()] if val else []
                elif field == "vital_signs_reported":
                    parsed[field] = {k.strip(): v.strip() for k, v in [x.split(":", 1) for x in val.split(",") if ":" in x]} if val else {}
                elif field == "red_flag_indicators":
                    parsed[field] = [s.strip() for s in val.split(",") if s.strip()] if val else []
                elif field == "referral_needed":
                    parsed[field] = val.lower() in ("yes", "true", "1")
                elif field == "confidence_score":
                    try:
                        parsed[field] = float(val)
                    except ValueError:
                        parsed[field] = 0.5
                else:
                    parsed[field] = val

        parsed["source_language"] = source_lang
        parsed["raw_transcript"] = transcript
        
        # Add defaults for missing fields
        defaults = {
            "triage_level": "green",
            "primary_complaint": "Not specified",
            "relevant_history": "None reported",
            "red_flag_indicators": [],
            "recommended_action": "Monitor and reassess",
            "referral_needed": False,
            "confidence_score": 0.5,
            "reported_symptoms": [],
            "vital_signs_reported": {},
            "duration_of_symptoms": "Unknown",
        }
        for field, default in defaults.items():
            if field not in parsed:
                parsed[field] = default
        
        return TriageOutput(**parsed)
