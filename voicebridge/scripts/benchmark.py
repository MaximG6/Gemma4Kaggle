"""
VoiceBridge Benchmark Suite
=======================================
Loads test cases from data/benchmark_cases.json (100 cases, 20 per SATS level,
5 languages).

Measures:
  - Triage accuracy        — % of cases where predicted level == expected
  - Safe escalation rate   — % of cases where predicted >= expected
  - Per-level accuracy     — breakdown across RED/ORANGE/YELLOW/GREEN/BLUE
  - Per-language accuracy  — breakdown across 5 languages
  - SATS validator agreement

Used by compare_models.py for real GGUF inference benchmarking.

Usage (from voicebridge/ repo root):
    python scripts/benchmark.py        # runs mock classifier
    python scripts/benchmark.py --help
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from data.clinical_validation import validate_triage
from pipeline.triage import TriageOutput

# ---------------------------------------------------------------------------
# Load test cases from JSON
# ---------------------------------------------------------------------------

_CASES_PATH = _REPO_ROOT / "data" / "benchmark_cases.json"

def _load_cases() -> list[dict]:
    if not _CASES_PATH.exists():
        raise FileNotFoundError(
            f"Benchmark cases not found at {_CASES_PATH}. "
            "Make sure data/benchmark_cases.json exists."
        )
    with open(_CASES_PATH, encoding="utf-8") as f:
        cases = json.load(f)
    return cases

TEST_CASES: list[dict] = _load_cases()

# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

_LEVEL_ORDER = {"blue": 0, "green": 1, "yellow": 2, "orange": 3, "red": 4}


def _is_safe(predicted: str, expected: str) -> bool:
    """Over-triage is safe. Under-triage is not."""
    return _LEVEL_ORDER.get(predicted, 0) >= _LEVEL_ORDER.get(expected, 0)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AccuracyResult:
    n:               int
    accuracy:        float
    safe_rate:       float
    unsafe_count:    int
    per_level:       dict[str, dict] = field(default_factory=dict)
    per_language:    dict[str, dict] = field(default_factory=dict)
    validator_agree: float           = 0.0
    case_results:    list[dict]      = field(default_factory=list)


# ---------------------------------------------------------------------------
# Accuracy runner — works with any classifier that has classify_case()
# ---------------------------------------------------------------------------

def run_accuracy(clf) -> AccuracyResult:
    per_level:    dict[str, list[bool]] = {l: [] for l in _LEVEL_ORDER}
    per_language: dict[str, list[bool]] = {}
    case_results: list[dict]            = []
    validator_safe: list[bool]          = []

    for case in TEST_CASES:
        output, _ = clf.classify_case(case)

        # Support both TriageOutput objects and plain strings
        if hasattr(output, "triage_level"):
            tl = output.triage_level
            predicted = tl.value if hasattr(tl, "value") else str(tl)
        else:
            predicted = str(output)

        expected = case["level"]
        correct  = predicted == expected
        safe     = _is_safe(predicted, expected)

        val = validate_triage(
            llm_colour=predicted,
            vital_signs=case["vitals"],
            red_flags=case["flags"],
            transcript_english=case["text_en"],
            language=case["lang"],
        )
        validator_safe.append(val.conflict_direction != "llm_under_triaged")

        per_level[expected].append(correct)
        per_language.setdefault(case["lang"], []).append(correct)

        case_results.append({
            "id":             case["id"],
            "lang":           case["lang"],
            "expected":       expected,
            "predicted":      predicted,
            "correct":        correct,
            "safe":           safe,
            "validator_safe": validator_safe[-1],
            "conflict":       val.conflict,
            "conflict_dir":   val.conflict_direction,
            "rule_colour":    val.rule_colour,
            "tews_score":     val.tews_score,
            "note":           case.get("note", ""),
        })

    n            = len(TEST_CASES)
    correct_all  = [r["correct"] for r in case_results]
    safe_all     = [r["safe"]    for r in case_results]
    unsafe_count = sum(1 for s in safe_all if not s)

    per_level_summary = {
        lvl: {
            "n":        len(v),
            "correct":  sum(v),
            "accuracy": round(sum(v) / len(v), 3) if v else 0.0,
        }
        for lvl, v in per_level.items() if v
    }
    per_lang_summary = {
        lang: {
            "n":        len(v),
            "correct":  sum(v),
            "accuracy": round(sum(v) / len(v), 3) if v else 0.0,
        }
        for lang, v in per_language.items()
    }

    return AccuracyResult(
        n=n,
        accuracy=round(sum(correct_all) / n, 3),
        safe_rate=round(sum(safe_all) / n, 3),
        unsafe_count=unsafe_count,
        per_level=per_level_summary,
        per_language=per_lang_summary,
        validator_agree=round(sum(validator_safe) / n, 3),
        case_results=case_results,
    )


# ---------------------------------------------------------------------------
# Mock classifier (for testing without a real model)
# ---------------------------------------------------------------------------

_MOCK_PREDICTIONS: dict[str, str] = {
    # RED
    "R01": "red",    "R02": "red",    "R03": "red",    "R04": "red",
    "R05": "red",    "R06": "red",    "R07": "red",    "R08": "red",
    "R09": "red",    "R10": "red",    "R11": "red",    "R12": "red",
    "R13": "red",    "R14": "red",    "R15": "red",    "R16": "red",
    "R17": "red",    "R18": "red",    "R19": "red",    "R20": "red",
    # ORANGE
    "O01": "orange", "O02": "orange", "O03": "red",    "O04": "red",
    "O05": "orange", "O06": "orange", "O07": "orange", "O08": "orange",
    "O09": "orange", "O10": "orange", "O11": "orange", "O12": "orange",
    "O13": "orange", "O14": "orange", "O15": "orange", "O16": "orange",
    "O17": "orange", "O18": "orange", "O19": "orange", "O20": "orange",
    # YELLOW
    "Y01": "yellow", "Y02": "yellow", "Y03": "orange", "Y04": "yellow",
    "Y05": "yellow", "Y06": "yellow", "Y07": "yellow", "Y08": "yellow",
    "Y09": "yellow", "Y10": "yellow", "Y11": "yellow", "Y12": "yellow",
    "Y13": "yellow", "Y14": "yellow", "Y15": "yellow", "Y16": "yellow",
    "Y17": "yellow", "Y18": "yellow", "Y19": "yellow", "Y20": "yellow",
    # GREEN
    "G01": "green",  "G02": "green",  "G03": "green",  "G04": "yellow",
    "G05": "green",  "G06": "green",  "G07": "green",  "G08": "green",
    "G09": "green",  "G10": "green",  "G11": "green",  "G12": "green",
    "G13": "green",  "G14": "green",  "G15": "green",  "G16": "green",
    "G17": "green",  "G18": "green",  "G19": "green",  "G20": "green",
    # BLUE
    "B01": "blue",   "B02": "blue",   "B03": "red",    "B04": "blue",
    "B05": "blue",   "B06": "blue",   "B07": "blue",   "B08": "blue",
    "B09": "blue",   "B10": "blue",   "B11": "blue",   "B12": "blue",
    "B13": "blue",   "B14": "blue",   "B15": "blue",   "B16": "blue",
    "B17": "blue",   "B18": "blue",   "B19": "blue",   "B20": "blue",
}


class MockTriageClassifier:
    def classify_case(self, case: dict) -> tuple[TriageOutput, float]:
        predicted = _MOCK_PREDICTIONS.get(case["id"], "green")
        output = TriageOutput(
            triage_level=predicted,
            primary_complaint=case["text_en"][:120],
            reported_symptoms=[],
            vital_signs_reported={k: str(v) for k, v in case["vitals"].items()},
            duration_of_symptoms="unknown",
            relevant_history="",
            red_flag_indicators=case["flags"],
            recommended_action="See within appropriate timeframe",
            referral_needed=predicted in ("red", "orange"),
            confidence_score=0.92,
            source_language=case["lang"],
            raw_transcript=case["text_en"],
        )
        return output, 0.0


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def _bar(value: float, width: int = 20) -> str:
    filled = round(value * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def print_report(acc: AccuracyResult) -> None:
    print()
    print("\u2554" + "\u2550" * 62 + "\u2557")
    print("\u2551         VoiceBridge Benchmark Results (100 cases)          \u2551")
    print("\u255a" + "\u2550" * 62 + "\u255d")

    print(f"\n\u2500\u2500 Triage Accuracy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    print(f"  Total cases           : {acc.n}")
    print(f"  Exact match accuracy  : {acc.accuracy:.1%}  {_bar(acc.accuracy)}")
    print(f"  Safe escalation rate  : {acc.safe_rate:.1%}  {_bar(acc.safe_rate)}")
    print(f"  Unsafe under-calls    : {acc.unsafe_count}  (target: 0)")
    print(f"  SATS validator agree  : {acc.validator_agree:.1%}  {_bar(acc.validator_agree)}")

    print(f"\n\u2500\u2500 Per-Level Accuracy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    for lvl in ["red", "orange", "yellow", "green", "blue"]:
        if lvl in acc.per_level:
            s = acc.per_level[lvl]
            print(f"  {lvl.upper():<10}  {s['correct']}/{s['n']}  {s['accuracy']:.0%}  {_bar(s['accuracy'])}")

    print(f"\n\u2500\u2500 Per-Language Accuracy \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    lang_names = {"en": "English", "sw": "Swahili", "ha": "Hausa", "tl": "Tagalog", "bn": "Bengali"}
    for lang, s in sorted(acc.per_language.items()):
        name = lang_names.get(lang, lang.upper())
        print(f"  {name:<10}  {s['correct']}/{s['n']}  {s['accuracy']:.0%}  {_bar(s['accuracy'])}")

    print()
    if acc.unsafe_count > 0:
        print(f"  \u26a0  {acc.unsafe_count} unsafe under-triage case(s) detected")
    else:
        print("  \u2713  No unsafe under-triage cases detected")
    print()


# ---------------------------------------------------------------------------
# Main (mock run for quick validation)
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="VoiceBridge benchmark suite")
    parser.add_argument("--cases-path", type=str, default=str(_CASES_PATH),
                        help="Path to benchmark_cases.json")
    args = parser.parse_args()

    print(f"Loading cases from: {args.cases_path}")
    print(f"Running mock benchmark on {len(TEST_CASES)} cases ...", flush=True)

    clf = MockTriageClassifier()
    acc = run_accuracy(clf)
    print_report(acc)

    out_path = _REPO_ROOT / "docs" / "benchmark_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "meta": {
            "test_cases": acc.n,
            "simulated":  True,
            "note":       "Mock classifier — real numbers from compare_models.py",
        },
        "accuracy": {
            "overall":             acc.accuracy,
            "safe_rate":           acc.safe_rate,
            "unsafe_count":        acc.unsafe_count,
            "validator_agreement": acc.validator_agree,
            "per_level":           acc.per_level,
            "per_language":        acc.per_language,
        },
        "cases": acc.case_results,
    }, indent=2))
    print(f"Results saved \u2192 {out_path.relative_to(_REPO_ROOT)}")


if __name__ == "__main__":
    main()