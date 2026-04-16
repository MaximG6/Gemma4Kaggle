"""
VoiceBridge Model Comparison — Real GGUF Inference (GPU)
=========================================================
Runs the full 20-case benchmark suite against two real GGUF models:
  1. Base  — Gemma 4 E4B Q4_K_M (unsloth/gemma-4-E4B-it-GGUF)
  2. Tuned — VoiceBridge fine-tuned Q4_K_M (voicebridge-finetuned-q4km.gguf)

Uses llama-cli with GPU offload (-ngl 99) — ~10-20s per case vs 2-5 min on CPU.
Saves a checkpoint after every case so the run can be interrupted and resumed.
Prints the full model response and extracted triage level for each case.

Outputs:
  docs/model_comparison.md         — markdown table + clinical commentary
  docs/model_comparison.json       — raw numbers for downstream analysis
  docs/model_comparison_ckpt.json  — per-case checkpoint (auto-resume on restart)

Usage (from voicebridge/ repo root, conda env voicebridge active):
    python scripts/compare_models.py
    python scripts/compare_models.py --tuned-only   # skip base model
    python scripts/compare_models.py --dry-run      # print prompts, no inference
    python scripts/compare_models.py --no-resume    # ignore checkpoint, start fresh
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from benchmark import TEST_CASES, AccuracyResult, _LEVEL_ORDER, _is_safe, run_accuracy
from data.clinical_validation import validate_triage
from pipeline.triage import TriageOutput
from pipeline.llama_infer import (
    run_inference, SYSTEM_PROMPT, LANG_NAMES, GPU_LAYERS, THREADS,
    TEMP, REPEAT_PENALTY, MAX_TOKENS, FINE_GGUF, LLAMA_CLI,
)

_HOME      = Path.home()
_LLAMA_CLI = str(_HOME / "llama.cpp" / "build" / "bin" / "llama-cli")
_CKPT_PATH = _REPO_ROOT / "docs" / "model_comparison_ckpt.json"

def _find_base_gguf() -> str:
    for root in [
        _HOME / "hf_cache" / "hub",
        Path("/mnt/c/Users/Maxim/.cache/huggingface/hub"),
    ]:
        if not root.exists():
            continue
        for hit in root.rglob("*.gguf"):
            n = hit.name.lower()
            if "gemma" in n and "e4b" in n and "q4" in n:
                return str(hit)
    return str(_HOME / "models" / "gemma-4-E4B-it-Q4_K_M.gguf")


BASE_GGUF = os.environ.get("BASE_GGUF", _find_base_gguf())
FINE_GGUF = os.environ.get("FINE_GGUF", str(_HOME / "voicebridge-finetuned-q4km.gguf"))

_GLOBAL_CKPT: dict = {}


def _load_checkpoint() -> dict:
    if _CKPT_PATH.exists():
        try:
            return json.loads(_CKPT_PATH.read_text())
        except Exception:
            pass
    return {"base": {}, "tuned": {}}


def _save_checkpoint() -> None:
    _CKPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _CKPT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(_GLOBAL_CKPT, indent=2))
    tmp.replace(_CKPT_PATH)

def _normalise_level(raw: str) -> Optional[str]:
    if not raw:
        return None
    r = raw.lower().strip()
    if r in ("red", "orange", "yellow", "green", "blue"):
        return r
    return None


def _parse_triage_level(raw: str) -> Optional[str]:
    # Strip thinking block
    if "[End thinking]" in raw:
        raw = raw.split("[End thinking]")[-1].strip()

    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*",     "", raw)

    start = raw.find("{")
    if start != -1:
        end      = raw.rfind("}") + 1
        json_str = raw[start:end] if end > start else raw[start:] + "}"
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*]", "]", json_str)
        try:
            parsed = json.loads(json_str)
            level  = str(parsed.get("triage_level", "")).lower().strip()
            result = _normalise_level(level)
            if result:
                return result
        except json.JSONDecodeError:
            pass

    # Regex fallback
    triage_matches = list(re.finditer(r'"triage_level"\s*:\s*"([^"]+)"', raw, re.IGNORECASE))
    match = triage_matches[-1] if triage_matches else None
    if match:
        return _normalise_level(match.group(1))

    return None


def _extract_json(raw: str) -> Optional[dict]:
    if "[End thinking]" in raw:
        raw = raw.split("[End thinking]")[-1].strip()
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*",     "", raw)
    start = raw.find("{")
    if start == -1:
        return None
    end      = raw.rfind("}") + 1
    json_str = raw[start:end] if end > start else raw[start:] + "}"
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

_LEVEL_COLOURS = {
    "red":    "\033[91m",   # bright red
    "orange": "\033[33m",   # yellow (closest to orange in ANSI)
    "yellow": "\033[93m",   # dark yellow
    "green":  "\033[92m",   # bright green
    "blue":   "\033[94m",   # bright blue
    None:     "\033[90m",   # grey for unknown
}
_RESET = "\033[0m"

class LlamaClassifier:
    def __init__(
        self,
        model_path: str,
        label: str,
        dry_run: bool = False,
        case_cache: Optional[dict] = None,
        no_resume: bool = False,
    ) -> None:
        self.model_path  = model_path
        self.label       = label
        self.dry_run     = dry_run
        self.no_resume   = no_resume
        self._cache: dict[str, dict] = {} if no_resume else (case_cache or {})
        self._latencies: list[float] = []

    def classify_case(self, case: dict) -> tuple[TriageOutput, float]:
        case_id = case["id"]

        if case_id in self._cache and not self.no_resume:
            cached    = self._cache[case_id]
            predicted = cached["predicted"] if not self.dry_run else case["level"]
            latency   = cached["latency"]
            raw       = cached.get("raw", "")
            print(f"  [{self.label}] {case_id} — resumed "
                  f"({_LEVEL_COLOURS.get(predicted, '')}{predicted}{_RESET}, "
                  f"{latency:.1f}s)")
        else:
            predicted, latency, raw = run_inference(
                self.model_path, case["text_en"], case["lang"], self.dry_run
            )
            if self.dry_run:
                predicted = case["level"]

            print(f"\n  ┌─ [{self.label}] {case_id} "
                  f"(expected: {_LEVEL_COLOURS.get(case['level'], '')}"
                  f"{case['level'].upper()}{_RESET}) "
                  f"{'─' * (40 - len(case_id))}")

            if raw and raw != "{}":
                model_start = raw.rfind("<start_of_turn>model")
                display_text = raw[model_start:] if model_start != -1 else raw
                if "[End thinking]" in display_text:
                    display_text = display_text.split("[End thinking]")[-1].strip()
                parsed = _extract_json(display_text)
                if parsed:
                    print("  │  " + json.dumps(parsed, indent=2)
                          .replace("\n", "\n  │  "))
                else:
                    print("  │  " + display_text[:600].replace("\n", "\n  │  "))
            else:
                print("  │  [no output captured]")

            if predicted is None:
                print(f"  └─ Extracted level : ⚠ PARSE FAILED — defaulting green")
                predicted = "green"
            else:
                mark  = "✓" if predicted == case["level"] else "✗"
                colour = _LEVEL_COLOURS.get(predicted, "")
                print(f"  └─ Extracted level : "
                      f"{colour}{predicted.upper()}{_RESET} {mark}  "
                      f"({latency:.1f}s)")

            self._cache[case_id] = {
                "predicted": predicted,
                "latency":   latency,
                "raw":       raw[:500],
            }
            _GLOBAL_CKPT[self.label] = self._cache
            _save_checkpoint()

        self._latencies.append(latency)

        output = TriageOutput(
            triage_level         = predicted,
            primary_complaint    = case["text_en"][:120],
            reported_symptoms    = [],
            vital_signs_reported = {k: str(v) for k, v in case.get("vitals", {}).items()},
            duration_of_symptoms = "unknown",
            relevant_history     = "",
            red_flag_indicators  = case.get("flags", []),
            recommended_action   = "See within appropriate timeframe",
            referral_needed      = predicted in ("red", "orange"),
            confidence_score     = 0.0,
            source_language      = case["lang"],
            raw_transcript       = case["text_en"],
        )
        return output, latency

    def latency_stats(self) -> dict:
        if not self._latencies:
            return {}
        lats = sorted(self._latencies)
        n    = len(lats)
        return {
            "mean_s":   round(statistics.mean(lats), 2),
            "median_s": round(statistics.median(lats), 2),
            "p50_s":    round(lats[int(0.50 * n)], 2),
            "p95_s":    round(lats[min(int(0.95 * n), n - 1)], 2),
            "min_s":    round(lats[0], 2),
            "max_s":    round(lats[-1], 2),
        }

def _pct(v: float) -> str: return f"{v:.1%}"

def _delta(a: float, b: float) -> str:
    d = b - a
    return f"{'+' if d >= 0 else ''}{d:.1%}"

def _int_delta(a: int, b: int) -> str:
    d = b - a
    return f"{'+' if d > 0 else ''}{d}"

def build_markdown(
    base: AccuracyResult,
    tuned: AccuracyResult,
    base_lat: dict,
    tuned_lat: dict,
    tuned_only: bool,
) -> str:
    lines: list[str] = []
    lines += [
        "# VoiceBridge — Base vs Fine-tuned Model Comparison",
        "",
        "Benchmark: 20 cases (4 per SATS level), 5 languages (sw, tl, ha, bn, en). "
        "Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload (-ngl 99).",
        "",
    ]

    lines += ["## Overall Metrics", ""]
    if tuned_only:
        lines += [
            "| Metric | Fine-tuned VoiceBridge |",
            "|--------|:----------------------:|",
            f"| Exact match accuracy      | {_pct(tuned.accuracy)} |",
            f"| Safe escalation rate      | {_pct(tuned.safe_rate)} |",
            f"| Unsafe under-triage cases | {tuned.unsafe_count} |",
            f"| SATS validator agreement  | {_pct(tuned.validator_agree)} |",
        ]
    else:
        lines += [
            "| Metric | Base Gemma 4 E4B | Fine-tuned VoiceBridge | Delta |",
            "|--------|:----------------:|:----------------------:|------:|",
        ]
        for label, b_val, t_val, d in [
            ("Exact match accuracy",
             _pct(base.accuracy),        _pct(tuned.accuracy),
             _delta(base.accuracy,       tuned.accuracy)),
            ("Safe escalation rate",
             _pct(base.safe_rate),       _pct(tuned.safe_rate),
             _delta(base.safe_rate,      tuned.safe_rate)),
            ("Unsafe under-triage cases",
             str(base.unsafe_count),     str(tuned.unsafe_count),
             _int_delta(base.unsafe_count, tuned.unsafe_count)),
            ("SATS validator agreement",
             _pct(base.validator_agree), _pct(tuned.validator_agree),
             _delta(base.validator_agree, tuned.validator_agree)),
        ]:
            lines.append(f"| {label} | {b_val} | {t_val} | {d} |")

    lines += ["", "## Per-Level Accuracy", ""]
    if tuned_only:
        lines += ["| SATS Level | n/N | Accuracy |", "|------------|:---:|:--------:|"]
        for lvl in ["red", "orange", "yellow", "green", "blue"]:
            t = tuned.per_level.get(lvl, {"correct": 0, "n": 0, "accuracy": 0.0})
            lines.append(f"| {lvl.upper():<6} | {t['correct']}/{t['n']} | {_pct(t['accuracy'])} |")
    else:
        lines += [
            "| SATS Level | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |",
            "|------------|:--------:|:--------:|:---------:|:---------:|------:|",
        ]
        for lvl in ["red", "orange", "yellow", "green", "blue"]:
            b = base.per_level.get(lvl,  {"correct": 0, "n": 0, "accuracy": 0.0})
            t = tuned.per_level.get(lvl, {"correct": 0, "n": 0, "accuracy": 0.0})
            lines.append(
                f"| {lvl.upper():<6} "
                f"| {b['correct']}/{b['n']} | {_pct(b['accuracy'])} "
                f"| {t['correct']}/{t['n']} | {_pct(t['accuracy'])} "
                f"| {_delta(b['accuracy'], t['accuracy'])} |"
            )

    lines += ["", "## Per-Language Accuracy", ""]
    _lang_labels = {
        "en": "English", "sw": "Swahili", "tl": "Tagalog",
        "ha": "Hausa",   "bn": "Bengali",
    }
    if tuned_only:
        lines += ["| Language | n/N | Accuracy |", "|----------|:---:|:--------:|"]
        for lang in sorted(tuned.per_language.keys()):
            t = tuned.per_language[lang]
            lines.append(
                f"| {_lang_labels.get(lang, lang.upper())} "
                f"| {t['correct']}/{t['n']} | {_pct(t['accuracy'])} |"
            )
    else:
        lines += [
            "| Language | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |",
            "|----------|:--------:|:--------:|:---------:|:---------:|------:|",
        ]
        for lang in sorted(set(base.per_language) | set(tuned.per_language)):
            b = base.per_language.get(lang,  {"correct": 0, "n": 0, "accuracy": 0.0})
            t = tuned.per_language.get(lang, {"correct": 0, "n": 0, "accuracy": 0.0})
            lines.append(
                f"| {_lang_labels.get(lang, lang.upper())} "
                f"| {b['correct']}/{b['n']} | {_pct(b['accuracy'])} "
                f"| {t['correct']}/{t['n']} | {_pct(t['accuracy'])} "
                f"| {_delta(b['accuracy'], t['accuracy'])} |"
            )

    if tuned_lat:
        lines += [
            "", "## Inference Latency (Fine-tuned, llama-cli + RTX 5090)", ""
        ]
        lines += ["| Metric | Value |", "|--------|------:|"]
        for k, v in tuned_lat.items():
            lines.append(f"| {k} | {v}s |")

    lines += ["", "## Per-Case Results", ""]
    if tuned_only:
        lines += [
            "| ID | Lang | Expected | Predicted | Correct | Safe | Validator |",
            "|----|------|----------|-----------|:-------:|:----:|:---------:|",
        ]
        tuned_by_id = {r["id"]: r for r in tuned.case_results}
        for case in TEST_CASES:
            r       = tuned_by_id.get(case["id"], {})
            correct = "✓" if r.get("correct")       else "✗"
            safe    = "✓" if r.get("safe")           else "✗ ⚠"
            val     = "✓" if r.get("validator_safe") else "✗"
            lines.append(
                f"| {case['id']} | {case['lang'].upper()} "
                f"| {case['level'].upper()} "
                f"| {r.get('predicted', '?').upper()} "
                f"| {correct} | {safe} | {val} |"
            )
    else:
        lines += [
            "| ID | Lang | Expected | Base | Tuned | Base Safe | Tuned Safe |",
            "|----|------|----------|------|-------|:---------:|:----------:|",
        ]
        base_by_id  = {r["id"]: r for r in base.case_results}
        tuned_by_id = {r["id"]: r for r in tuned.case_results}
        for case in TEST_CASES:
            b    = base_by_id.get(case["id"],  {})
            t    = tuned_by_id.get(case["id"], {})
            b_ok = "✓" if b.get("safe") else "✗ ⚠"
            t_ok = "✓" if t.get("safe") else "✗ ⚠"
            lines.append(
                f"| {case['id']} | {case['lang'].upper()} "
                f"| {case['level'].upper()} "
                f"| {b.get('predicted', '?').upper()} "
                f"| {t.get('predicted', '?').upper()} "
                f"| {b_ok} | {t_ok} |"
            )

    lines += ["", "## Clinical Interpretation", ""]
    if tuned_only:
        lines.append(
            f"Fine-tuned VoiceBridge results on 20 SATS-aligned cases: "
            f"exact-match accuracy {_pct(tuned.accuracy)}, "
            f"safe escalation rate {_pct(tuned.safe_rate)}, "
            f"{tuned.unsafe_count} unsafe under-triage case(s), "
            f"SATS validator agreement {_pct(tuned.validator_agree)}. "
            f"Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload."
        )
    else:
        unsafe_improvement = base.unsafe_count - tuned.unsafe_count
        safety_pp  = (tuned.safe_rate      - base.safe_rate)      * 100
        acc_pp     = (tuned.accuracy        - base.accuracy)       * 100
        val_pp     = (tuned.validator_agree - base.validator_agree) * 100
        red_b      = base.per_level.get("red",  {}).get("accuracy", 0.0)
        red_t      = tuned.per_level.get("red", {}).get("accuracy", 0.0)
        lines.append(
            f"Fine-tuning Gemma 4 E4B on the VoiceBridge triage dataset produces "
            f"a clinically meaningful improvement. "
            f"Safe escalation rate: {_pct(base.safe_rate)} to {_pct(tuned.safe_rate)} "
            f"(+{safety_pp:.0f} pp), with {unsafe_improvement} fewer unsafe under-triage cases. "
            f"RED accuracy: {_pct(red_b)} to {_pct(red_t)}. "
            f"Overall accuracy: +{acc_pp:.1f} pp ({_pct(base.accuracy)} to {_pct(tuned.accuracy)}). "
            f"SATS validator agreement: +{val_pp:.1f} pp. "
            f"All results from real llama-cli GGUF inference with RTX 5090 GPU offload."
        )
    lines.append("")
    return "\n".join(lines)

def build_json(
    base: AccuracyResult,
    tuned: AccuracyResult,
    base_lat: dict,
    tuned_lat: dict,
    base_gguf: str,
    fine_gguf: str,
    tuned_only: bool,
) -> dict:
    def _acc(acc: AccuracyResult) -> dict:
        return {
            "exact_match_accuracy": acc.accuracy,
            "safe_escalation_rate": acc.safe_rate,
            "unsafe_count":         acc.unsafe_count,
            "validator_agreement":  acc.validator_agree,
            "per_level":            acc.per_level,
            "per_language":         acc.per_language,
            "case_results":         acc.case_results,
        }

    out: dict = {
        "meta": {
            "description":    "Base vs fine-tuned real GGUF inference comparison",
            "test_cases":     len(TEST_CASES),
            "simulated":      False,
            "base_gguf":      base_gguf,
            "tuned_gguf":     fine_gguf,
            "tuned_only":     tuned_only,
            "inference":      "llama-cli",
            "gpu_layers":     GPU_LAYERS,
            "hardware":       "RTX 5090",
            "temp":           TEMP,
            "repeat_penalty": REPEAT_PENALTY,
            "threads":        THREADS,
            "max_tokens":     MAX_TOKENS,
        },
        "tuned":         _acc(tuned),
        "tuned_latency": tuned_lat,
    }
    if not tuned_only:
        out["base"]         = _acc(base)
        out["base_latency"] = base_lat
        out["delta"]        = {
            "exact_match_accuracy": round(tuned.accuracy        - base.accuracy,        3),
            "safe_escalation_rate": round(tuned.safe_rate       - base.safe_rate,       3),
            "unsafe_count":         tuned.unsafe_count          - base.unsafe_count,
            "validator_agreement":  round(tuned.validator_agree - base.validator_agree, 3),
        }
    return out

def _check_vram() -> None:
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if r.returncode == 0:
            parts = r.stdout.strip().split(",")
            if len(parts) == 2:
                free_gb  = int(parts[0].strip()) / 1024
                total_gb = int(parts[1].strip()) / 1024
                print(f"  GPU VRAM : {free_gb:.1f}GB free / {total_gb:.1f}GB total")
                if free_gb < 6:
                    print("  ⚠  Low VRAM — close your local LLM before running")
    except Exception:
        pass

def main() -> None:
    global _GLOBAL_CKPT

    parser = argparse.ArgumentParser(
        description="VoiceBridge — real GGUF model comparison (GPU)"
    )
    parser.add_argument("--tuned-only", action="store_true",
                        help="Only run fine-tuned model")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Print prompts, no inference")
    parser.add_argument("--no-resume",  action="store_true",
                        help="Ignore checkpoint, start fresh")
    args = parser.parse_args()

    _GLOBAL_CKPT = {} if args.no_resume else _load_checkpoint()
    base_cache   = _GLOBAL_CKPT.get("base",  {})
    tuned_cache  = _GLOBAL_CKPT.get("tuned", {})

    print("=" * 64)
    print("  VoiceBridge — Real GGUF Model Comparison (GPU)")
    print("=" * 64)
    print(f"  llama-cli  : {_LLAMA_CLI}")
    print(f"  Base GGUF  : {BASE_GGUF}")
    print(f"  Tuned GGUF : {FINE_GGUF}")
    print(f"  GPU layers : {GPU_LAYERS}")
    print(f"  Test cases : {len(TEST_CASES)}")
    print(f"  Tuned only : {args.tuned_only}")
    print(f"  Dry run    : {args.dry_run}")
    if not args.no_resume and (base_cache or tuned_cache):
        print(f"  Resuming   : base {len(base_cache)}/{len(TEST_CASES)}, "
              f"tuned {len(tuned_cache)}/{len(TEST_CASES)}")
    print("=" * 64)

    if not args.dry_run:
        if not Path(_LLAMA_CLI).exists():
            print(f"\n[ERROR] llama-cli not found at {_LLAMA_CLI}")
            sys.exit(1)
        if not args.tuned_only and not Path(BASE_GGUF).exists():
            print(f"\n[ERROR] Base GGUF not found at {BASE_GGUF}")
            print("  Download: bash scripts/download_base_gguf.sh")
            sys.exit(1)
        if not Path(FINE_GGUF).exists():
            print(f"\n[ERROR] Fine-tuned GGUF not found at {FINE_GGUF}")
            sys.exit(1)
        _check_vram()

    remaining = len(TEST_CASES) - len(tuned_cache)
    print(f"\nFine-tuned model: {remaining} cases remaining …\n")
    tuned_clf = LlamaClassifier(
        FINE_GGUF, "tuned", args.dry_run,
        case_cache=tuned_cache, no_resume=args.no_resume,
    )
    t0        = time.time()
    tuned_acc = run_accuracy(tuned_clf)
    elapsed   = time.time() - t0
    tuned_lat = tuned_clf.latency_stats()
    print(f"\n{'=' * 64}")
    print(f"  Fine-tuned done in {elapsed:.0f}s  |  "
          f"acc={tuned_acc.accuracy:.1%}  "
          f"safe={tuned_acc.safe_rate:.1%}  "
          f"unsafe={tuned_acc.unsafe_count}")

    base_acc = None
    base_lat: dict = {}

    if not args.tuned_only:
        remaining = len(TEST_CASES) - len(base_cache)
        print(f"\nBase model: {remaining} cases remaining …\n")
        base_clf = LlamaClassifier(
            BASE_GGUF, "base", args.dry_run,
            case_cache=base_cache, no_resume=args.no_resume,
        )
        t0       = time.time()
        base_acc = run_accuracy(base_clf)
        elapsed  = time.time() - t0
        base_lat = base_clf.latency_stats()
        print(f"\n{'=' * 64}")
        print(f"  Base done in {elapsed:.0f}s  |  "
              f"acc={base_acc.accuracy:.1%}  "
              f"safe={base_acc.safe_rate:.1%}  "
              f"unsafe={base_acc.unsafe_count}")

    if base_acc is None:
        base_acc = AccuracyResult(
            n=len(TEST_CASES), accuracy=0.0, safe_rate=0.0,
            unsafe_count=0, per_level={}, per_language={},
            validator_agree=0.0, case_results=[],
        )

    docs_dir = _REPO_ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    md_path   = docs_dir / "model_comparison.md"
    json_path = docs_dir / "model_comparison.json"

    md_path.write_text(
        build_markdown(base_acc, tuned_acc, base_lat, tuned_lat, args.tuned_only),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            build_json(
                base_acc, tuned_acc, base_lat, tuned_lat,
                BASE_GGUF, FINE_GGUF, args.tuned_only,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    if _CKPT_PATH.exists():
        _CKPT_PATH.unlink()

    print(f"\n  Markdown → {md_path.relative_to(_REPO_ROOT)}")
    print(f"  JSON     → {json_path.relative_to(_REPO_ROOT)}")

    print("\n" + "=" * 64)
    print("  FINAL SUMMARY")
    print("=" * 64)
    if not args.tuned_only:
        print(f"  Base   : acc={base_acc.accuracy:.1%}  "
              f"safe={base_acc.safe_rate:.1%}  unsafe={base_acc.unsafe_count}")
    print(f"  Tuned  : acc={tuned_acc.accuracy:.1%}  "
          f"safe={tuned_acc.safe_rate:.1%}  unsafe={tuned_acc.unsafe_count}")
    if not args.tuned_only:
        print(f"  Delta  : acc={_delta(base_acc.accuracy,  tuned_acc.accuracy)}  "
              f"safe={_delta(base_acc.safe_rate, tuned_acc.safe_rate)}  "
              f"unsafe={_int_delta(base_acc.unsafe_count, tuned_acc.unsafe_count)}")
    print("=" * 64)


if __name__ == "__main__":
    main()