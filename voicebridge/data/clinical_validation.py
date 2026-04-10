"""
VoiceBridge Clinical Validation Module
=======================================
Rule-based SATS 2023 cross-validator for LLM triage output.

This module implements two functions:
  1. _rule_based_sats()  — hard-coded TEWS thresholds + discriminator detection
  2. validate_triage()   — compares LLM output against rule-based result and
                           returns a ValidationResult with conflict flag and
                           recommended safe output.

All threshold values are sourced from:
  - Wallis et al., S Afr Med J, 2006 (original TEWS table)
  - Rominski et al., Afr J Emerg Med, 2014 (Ghana validation, confirms HR ranges)
  - EMSSA SATS Training Manual, 2012
  - Dixon et al., BMC Emerg Med, 2021 (prehospital validation)

Adult version only: patients > 12 years or > 150 cm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Constants — SATS colour ordering for comparison
# ---------------------------------------------------------------------------

COLOUR_ORDER = {"green": 0, "yellow": 1, "orange": 2, "red": 3, "blue": 4}

# Triage level → time-to-treatment target (minutes)
TIME_TO_TREATMENT: dict[str, str] = {
    "red":    "Immediate (0 min) — call physician now",
    "orange": "Within 10 minutes — senior nurse assessment",
    "yellow": "Within 60 minutes — nurse assessment",
    "green":  "Within 240 minutes — may be redirected to primary care",
    "blue":   "Deceased — manage per local protocol",
}


# ---------------------------------------------------------------------------
# Multilingual red flag keywords → immediate RED trigger
# ---------------------------------------------------------------------------

RED_FLAG_KEYWORDS: dict[str, list[str]] = {
    "en": [
        "not breathing", "stopped breathing", "no pulse", "unconscious",
        "fitting", "seizure", "convulsing", "unresponsive", "choking",
        "airway blocked", "heavy bleeding", "uncontrolled bleeding",
        "not responsive", "apnoeic", "apneic",
    ],
    "sw": [
        "hapumui", "anapumua vibaya sana", "hana mapigo ya moyo",
        "hana fahamu", "mshtuko", "kutoka damu nyingi",
        "kizuizi cha njia ya hewa", "hana uhai",
    ],
    "tl": [
        "hindi humihinga", "walang tibok ng puso", "walang malay",
        "nagse-seizure", "nanghihina ng todo", "matinding pagdurugo",
        "hindi sumasagot",
    ],
    "ha": [
        "baya numfashi", "babu bugun zuciya", "baya sani",
        "farfadiya", "zubar da jini mai yawa", "ba ya mayar da martani",
    ],
    "bn": [
        "শ্বাস নিচ্ছে না", "নাড়ি নেই", "অজ্ঞান",
        "খিঁচুনি", "অনেক রক্ত পড়ছে", "সাড়া দিচ্ছে না",
    ],
    "hi": [
        "सांस नहीं ले रहा", "नब्ज नहीं है", "बेहोश",
        "दौरा पड़ रहा है", "बहुत खून बह रहा है", "होश नहीं है",
    ],
    "am": [
        "አይተነፍስም", "ምት የለም", "ንቃተ ህሊና የለም",
        "የሚያናውጥ", "ብዙ ደም እየፈሰሰ", "ምላሽ አይሰጥም",
    ],
    "fr": [
        "ne respire pas", "pas de pouls", "inconscient",
        "convulsions", "saignement abondant", "ne répond pas",
        "arrêt respiratoire",
    ],
}

# Emergency discriminators (plain English — matched against transcript_english)
EMERGENCY_DISCRIMINATORS: list[str] = [
    "airway obstruction", "airway blocked", "apnoea", "apnea",
    "not breathing", "stopped breathing", "absent breathing",
    "active seizure", "active convulsion", "convulsing",
    "uncontrolled bleeding", "uncontrolled haemorrhage", "uncontrolled hemorrhage",
    "major haemorrhage", "major hemorrhage",
    "responds to pain only", "unresponsive", "avpu u", "avpu p",
    "high energy trauma", "high energy mechanism", "vehicle rollover",
    "ejection from vehicle", "fall greater than 3", "fall more than 3",
    "penetrating chest", "penetrating abdomen", "stab to chest",
    "stab to abdomen", "gunshot chest", "gunshot abdomen",
    "stab to neck", "gunshot to neck",
    "anaphylaxis", "stridor",
    "eclampsia", "seizure in pregnancy",
    "burns airway", "inhalation injury",
    "near drowning", "submersion",
]

VERY_URGENT_DISCRIMINATORS: list[str] = [
    "altered consciousness", "decreased consciousness", "confused",
    "gcs 9", "gcs 10", "gcs 11", "gcs 12", "gcs 13",
    "responds to voice", "avpu v",
    "suspected stroke", "facial droop", "arm weakness", "speech difficulty",
    "bleeding in pregnancy", "antepartum haemorrhage",
    "chest pain", "suspected heart attack", "suspected mi",
    "diabetic ketoacidosis", "dka",
    "severe pain",
]

URGENT_DISCRIMINATORS: list[str] = [
    "vomiting blood", "haematemesis", "hematemesis",
    "head injury", "loss of consciousness", "suspected fracture",
    "moderate pain",
    "suicidal", "psychosis", "acute psychiatric",
    "fever in infant", "fever in baby",
]


# ---------------------------------------------------------------------------
# TEWS calculation helpers
# ---------------------------------------------------------------------------

def _score_rr(rr: float) -> int:
    """Respiratory rate score. Source: SATS TEWS adult table."""
    if rr <= 8:
        return 3
    if rr <= 14:
        return 2
    if rr <= 24:
        return 0   # normal range
    if rr <= 29:
        return 1
    return 2       # >= 30


def _score_hr(hr: float) -> int:
    """Heart rate score. Source: SATS TEWS adult table, confirmed Rominski 2014."""
    if hr <= 40:
        return 3
    if hr <= 50:
        return 2
    if hr <= 99:
        return 0   # normal range
    if hr <= 110:
        return 1
    if hr <= 129:
        return 2
    return 3       # >= 130


def _score_sbp(sbp: float) -> int:
    """Systolic blood pressure score. Source: SATS TEWS adult table."""
    if sbp <= 70:
        return 3
    if sbp <= 80:
        return 2
    if sbp <= 100:
        return 1
    return 0       # >= 101, normal (high BP does not score in TEWS)


def _score_temp(temp: float) -> int:
    """Temperature score (°C). Can only be 0 or 2 — grey cells in SATS poster."""
    if temp < 35.0 or temp > 38.5:
        return 2
    return 0


def _score_avpu(avpu: str) -> int:
    """AVPU consciousness score."""
    avpu = avpu.strip().upper()
    if avpu == "U":
        return 3
    if avpu == "P":
        return 2
    if avpu == "V":
        return 1
    return 0   # A (Alert) or unknown defaults to 0


def _score_mobility(mobility: str) -> int:
    """
    Mobility score.
    Expected values: 'normal', 'assisted', 'carried'/'bedridden'
    """
    mobility = mobility.strip().lower()
    if mobility in ("carried", "bedridden", "unable", "cannot walk"):
        return 2
    if mobility in ("assisted", "help", "support"):
        return 1
    return 0


def _score_trauma(trauma: bool) -> int:
    """Trauma score: 1 if any injury in past 48 hours, else 0."""
    return 1 if trauma else 0


def _tews_to_colour(tews: int) -> str:
    """Map TEWS total to SATS colour. Source: Wallis 2006, Dixon 2021."""
    if tews <= 2:
        return "green"
    if tews <= 4:
        return "yellow"
    if tews <= 6:
        return "orange"
    return "red"


# ---------------------------------------------------------------------------
# SpO2 and glucose upgrade rules (Part 3 of SATS)
# ---------------------------------------------------------------------------

def _apply_additional_investigations(
    colour: str,
    spo2: Optional[float],
    glucose: Optional[float],
    avpu: str,
) -> str:
    """
    Apply SATS Part 3 additional investigation upgrade rules.
    Can only upgrade colour, never downgrade.
    """
    current_rank = COLOUR_ORDER.get(colour, 0)

    if spo2 is not None:
        if spo2 < 90.0:
            current_rank = max(current_rank, COLOUR_ORDER["red"])
        elif spo2 < 95.0:
            current_rank = max(current_rank, COLOUR_ORDER["orange"])

    if glucose is not None:
        avpu_rank = _score_avpu(avpu)
        if glucose < 3.0:
            if avpu_rank >= 1:   # V, P, or U — altered consciousness
                current_rank = max(current_rank, COLOUR_ORDER["red"])
            else:
                current_rank = max(current_rank, COLOUR_ORDER["orange"])
        elif glucose > 20.0:
            current_rank = max(current_rank, COLOUR_ORDER["orange"])

    # Reverse lookup
    for colour_name, rank in COLOUR_ORDER.items():
        if rank == current_rank:
            return colour_name
    return colour


# ---------------------------------------------------------------------------
# Discriminator detection
# ---------------------------------------------------------------------------

def _detect_discriminators(
    text: str,
    language: str = "en",
) -> tuple[str | None, list[str]]:
    """
    Check transcript against SATS discriminator lists and multilingual
    red flag keywords.

    Returns:
        (assigned_colour, matched_discriminators)
        assigned_colour is None if no discriminators matched.
    """
    text_lower = text.lower()
    matched: list[str] = []
    highest_colour: str | None = None

    # Check multilingual keywords (all languages in transcript)
    for lang, keywords in RED_FLAG_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                matched.append(f"[{lang}] {kw}")
                highest_colour = "red"

    # Check English emergency discriminators
    for disc in EMERGENCY_DISCRIMINATORS:
        if disc in text_lower:
            matched.append(disc)
            highest_colour = "red"

    # Check very urgent discriminators only if no RED found
    if highest_colour != "red":
        for disc in VERY_URGENT_DISCRIMINATORS:
            if disc in text_lower:
                matched.append(disc)
                if highest_colour != "orange":
                    highest_colour = "orange"

    # Check urgent discriminators only if no RED or ORANGE found
    if highest_colour not in ("red", "orange"):
        for disc in URGENT_DISCRIMINATORS:
            if disc in text_lower:
                matched.append(disc)
                highest_colour = "yellow"

    return highest_colour, matched


# ---------------------------------------------------------------------------
# Main rule-based SATS function
# ---------------------------------------------------------------------------

def _rule_based_sats(
    vital_signs: dict,
    red_flags: list[str],
    transcript_english: str = "",
    language: str = "en",
) -> tuple[str, int | None, list[str]]:
    """
    Cross-check against hard-coded SATS 2023 criteria.

    Args:
        vital_signs: dict with optional keys:
            rr    — respiratory rate (breaths/min)
            hr    — heart rate (beats/min)
            sbp   — systolic blood pressure (mmHg)
            temp  — temperature (°C)
            avpu  — string: 'A', 'V', 'P', or 'U'
            spo2  — oxygen saturation (%)
            glucose — blood glucose (mmol/L)
            mobility — string: 'normal', 'assisted', 'carried'
            trauma — bool
        red_flags: list of red flag strings from LLM output
        transcript_english: full English transcript for discriminator matching
        language: ISO 639-1 source language for multilingual keyword check

    Returns:
        (colour, tews_score_or_none, matched_discriminators)
    """
    # --- Step 1: Check discriminators (Part 1 of SATS) ---
    # Combine red_flags list and transcript for matching
    combined_text = " ".join(red_flags) + " " + transcript_english
    disc_colour, matched_discs = _detect_discriminators(combined_text, language)

    # If emergency discriminator found → RED immediately (no TEWS needed)
    if disc_colour == "red":
        return "red", None, matched_discs

    # --- Step 2: Calculate TEWS (Part 2 of SATS) ---
    tews = 0
    vitals_available = False

    rr = vital_signs.get("rr")
    hr = vital_signs.get("hr")
    sbp = vital_signs.get("sbp")
    temp = vital_signs.get("temp")
    avpu = vital_signs.get("avpu", "A")
    mobility = vital_signs.get("mobility", "normal")
    trauma = vital_signs.get("trauma", False)

    if rr is not None:
        tews += _score_rr(float(rr))
        vitals_available = True
    if hr is not None:
        tews += _score_hr(float(hr))
        vitals_available = True
    if sbp is not None:
        tews += _score_sbp(float(sbp))
        vitals_available = True
    if temp is not None:
        tews += _score_temp(float(temp))
        vitals_available = True

    tews += _score_avpu(str(avpu))
    tews += _score_mobility(str(mobility))
    tews += _score_trauma(bool(trauma))

    # If no numeric vitals reported, TEWS is unreliable
    tews_colour = _tews_to_colour(tews) if vitals_available else "green"
    tews_score = tews if vitals_available else None

    # --- Step 3: Apply additional investigations (Part 3 of SATS) ---
    spo2 = vital_signs.get("spo2")
    glucose = vital_signs.get("glucose")
    final_colour = _apply_additional_investigations(
        tews_colour, spo2, glucose, str(avpu)
    )

    # --- Step 4: Apply any non-RED discriminators ---
    if disc_colour is not None:
        disc_rank = COLOUR_ORDER.get(disc_colour, 0)
        final_rank = COLOUR_ORDER.get(final_colour, 0)
        if disc_rank > final_rank:
            final_colour = disc_colour

    return final_colour, tews_score, matched_discs


# ---------------------------------------------------------------------------
# Validation result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    llm_colour: str
    rule_colour: str
    tews_score: Optional[int]
    matched_discriminators: list[str]
    conflict: bool
    conflict_direction: str   # "none", "llm_under_triaged", "rule_under_triaged"
    safe_colour: str          # always the more urgent of the two
    warning_message: str
    time_to_treatment: str


# ---------------------------------------------------------------------------
# Public validate_triage function
# ---------------------------------------------------------------------------

def validate_triage(
    llm_colour: str,
    vital_signs: dict,
    red_flags: list[str],
    transcript_english: str = "",
    language: str = "en",
) -> ValidationResult:
    """
    Compare LLM triage output against rule-based SATS validator.

    The safe output is always the MORE urgent of the two levels.
    If they conflict, a warning is generated for display in the UI and PDF.

    Args:
        llm_colour: triage level from LLM (lowercase: 'red', 'orange', etc.)
        vital_signs: dict as described in _rule_based_sats()
        red_flags: list of red flag strings from LLM output
        transcript_english: English transcript for discriminator matching
        language: source language ISO code

    Returns:
        ValidationResult with safe_colour and conflict details
    """
    llm_colour = llm_colour.strip().lower()
    rule_colour, tews_score, matched_discs = _rule_based_sats(
        vital_signs, red_flags, transcript_english, language
    )

    llm_rank = COLOUR_ORDER.get(llm_colour, 0)
    rule_rank = COLOUR_ORDER.get(rule_colour, 0)

    conflict = llm_rank != rule_rank
    safe_colour = llm_colour if llm_rank >= rule_rank else rule_colour

    if not conflict:
        direction = "none"
        warning = ""
    elif llm_rank < rule_rank:
        direction = "llm_under_triaged"
        warning = (
            f"⚠️  SAFETY ALERT: Rule-based SATS validator assigned "
            f"{rule_colour.upper()} but LLM assigned {llm_colour.upper()}. "
            f"Output upgraded to {safe_colour.upper()}. "
            f"Senior clinician review required. "
            f"TEWS: {tews_score if tews_score is not None else 'N/A'}. "
            f"Matched: {'; '.join(matched_discs) if matched_discs else 'none'}."
        )
    else:
        direction = "rule_under_triaged"
        warning = (
            f"ℹ️  NOTE: LLM assigned {llm_colour.upper()} but rule-based "
            f"validator assigned {rule_colour.upper()}. "
            f"LLM output retained — may have detected narrative discriminators. "
            f"TEWS: {tews_score if tews_score is not None else 'N/A'}."
        )

    return ValidationResult(
        llm_colour=llm_colour,
        rule_colour=rule_colour,
        tews_score=tews_score,
        matched_discriminators=matched_discs,
        conflict=conflict,
        conflict_direction=direction,
        safe_colour=safe_colour,
        warning_message=warning,
        time_to_treatment=TIME_TO_TREATMENT.get(safe_colour, "Unknown"),
    )


# ---------------------------------------------------------------------------
# Convenience: score individual TEWS components for display
# ---------------------------------------------------------------------------

def explain_tews(vital_signs: dict) -> dict:
    """
    Return per-parameter TEWS scores for display in the PDF form.
    Useful for transparency — shows the nurse why a score was assigned.
    """
    rr = vital_signs.get("rr")
    hr = vital_signs.get("hr")
    sbp = vital_signs.get("sbp")
    temp = vital_signs.get("temp")
    avpu = vital_signs.get("avpu", "A")
    mobility = vital_signs.get("mobility", "normal")
    trauma = vital_signs.get("trauma", False)

    return {
        "rr_score":       _score_rr(float(rr)) if rr is not None else None,
        "hr_score":       _score_hr(float(hr)) if hr is not None else None,
        "sbp_score":      _score_sbp(float(sbp)) if sbp is not None else None,
        "temp_score":     _score_temp(float(temp)) if temp is not None else None,
        "avpu_score":     _score_avpu(str(avpu)),
        "mobility_score": _score_mobility(str(mobility)),
        "trauma_score":   _score_trauma(bool(trauma)),
        "tews_total":     sum(
            v for v in [
                _score_rr(float(rr)) if rr is not None else 0,
                _score_hr(float(hr)) if hr is not None else 0,
                _score_sbp(float(sbp)) if sbp is not None else 0,
                _score_temp(float(temp)) if temp is not None else 0,
                _score_avpu(str(avpu)),
                _score_mobility(str(mobility)),
                _score_trauma(bool(trauma)),
            ]
        ),
    }


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # RED case: RR=32, HR=140, AVPU=P → TEWS ≥ 7
    result = validate_triage(
        llm_colour="orange",
        vital_signs={"rr": 32, "hr": 140, "avpu": "P", "sbp": 85},
        red_flags=["difficulty breathing", "altered consciousness"],
        transcript_english="Patient is not responding to voice, responds to pain only, "
                           "breathing very fast at 32 breaths per minute.",
        language="en",
    )
    print("=== RED conflict test ===")
    print(f"LLM: {result.llm_colour} | Rule: {result.rule_colour} | "
          f"Safe: {result.safe_colour} | TEWS: {result.tews_score}")
    print(f"Warning: {result.warning_message}")
    print()

    # GREEN case: all normal
    result2 = validate_triage(
        llm_colour="green",
        vital_signs={"rr": 18, "hr": 78, "sbp": 118, "temp": 37.1, "avpu": "A"},
        red_flags=[],
        transcript_english="Patient is alert and oriented, complaining of mild headache.",
        language="en",
    )
    print("=== GREEN agreement test ===")
    print(f"LLM: {result2.llm_colour} | Rule: {result2.rule_colour} | "
          f"Safe: {result2.safe_colour} | TEWS: {result2.tews_score}")
    print(f"Conflict: {result2.conflict}")
    print()

    # SpO2 upgrade test: TEWS=2 (green) but SpO2=88 → should upgrade to RED
    result3 = validate_triage(
        llm_colour="yellow",
        vital_signs={"rr": 20, "hr": 95, "sbp": 110, "temp": 37.8,
                     "avpu": "A", "spo2": 88.0},
        red_flags=["low oxygen saturation"],
        transcript_english="Patient has oxygen saturation of 88 percent.",
        language="en",
    )
    print("=== SpO2 upgrade test ===")
    print(f"LLM: {result3.llm_colour} | Rule: {result3.rule_colour} | "
          f"Safe: {result3.safe_colour} | TEWS: {result3.tews_score}")
    print(f"Warning: {result3.warning_message}")

    # Swahili keyword test
    result4 = validate_triage(
        llm_colour="green",
        vital_signs={},
        red_flags=[],
        transcript_english="mgonjwa hapumui na hana mapigo ya moyo",
        language="sw",
    )
    print()
    print("=== Swahili RED keyword test ===")
    print(f"LLM: {result4.llm_colour} | Rule: {result4.rule_colour} | "
          f"Safe: {result4.safe_colour}")
    print(f"Matched: {result4.matched_discriminators}")
