"""
VoiceBridge — Quick Prompt & Parameter Tuner
=============================================
Runs 10 fixed cases against your fine-tuned GGUF with configurable
prompt and sampling parameters. Designed for fast iteration —
swap CONFIG values at the top and rerun to find the best combination.

Each run takes ~2-4 minutes on GPU. Prints a score and per-level breakdown.

Usage:
    conda activate voicebridge
    cd /path/to/voicebridge
    python scripts/prompt_tuner.py

    # Print full model response for each case:
    python scripts/prompt_tuner.py --verbose

    # Override model path:
    FINE_GGUF=~/my_model.gguf python scripts/prompt_tuner.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

_REPO_ROOT_PT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT_PT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_PT))

from pipeline.llama_infer import run_inference

# ===========================================================================
#  ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗
# ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝
# ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗
# ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║
# ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝
#  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝
#  Edit everything in this section. Nothing below the divider needs touching.
# ===========================================================================

# ── Model path ───────────────────────────────────────────────────────────────
FINE_GGUF = os.environ.get(
    "FINE_GGUF",
    str(Path.home() / "voicebridge-finetuned-q4km.gguf")
)
LLAMA_CLI = str(Path.home() / "llama.cpp" / "build" / "bin" / "llama-cli")

# ── Sampling parameters ──────────────────────────────────────────────────────
# Try different values to find what gives the most consistent JSON output.
TEMP           = 0.1    # 0.0 = fully deterministic, 0.2 = slight variation
REPEAT_PENALTY = 1.3    # penalise repeating tokens. try 1.1, 1.3, 1.5
MAX_TOKENS     = 1024    # max output length. try 300, 512, 600
GPU_LAYERS     = 99     # keep at 99 for RTX 5090
THREADS        = 4

# ── System prompt ─────────────────────────────────────────────────────────────
# Loaded from voicebridge/prompts/triage_system.txt — edit that file to change
# the prompt. compare_models.py reads the same file.

_PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "triage_system.txt"
SYSTEM_PROMPT = _PROMPT_FILE.read_text(encoding="utf-8")

# ===========================================================================
#  10 TEST CASES — 2 per level, covering 5 languages
#  Do not change the expected levels unless you disagree clinically.
# ===========================================================================

TEST_CASES = [
    # ── RED ──────────────────────────────────────────────────────────────────
    {
        "id": "R1", "level": "red", "lang": "en",
        "text": "Patient not breathing, no pulse, lips blue. Bystander CPR in progress.",
    },
    {
        "id": "R2", "level": "red", "lang": "sw",
        "text": "Mtoto wa miaka 3 ana degedege la dakika 8. Hajui chochote. Homa kali.",
    },
    # ── ORANGE ───────────────────────────────────────────────────────────────
    {
        "id": "O1", "level": "orange", "lang": "en",
        "text": (
            "Adult male. Central chest pain 45 min, radiates to left arm. "
            "Sweating. HR 112, RR 22, BP 130/85. Fully alert and talking."
        ),
    },
    {
        "id": "O2", "level": "orange", "lang": "tl",
        "text": (
            "Babae, 55 taong gulang. Biglaang kahinaan ng kanang braso at "
            "pagbagsak ng mukha, 1 oras na. Nakakapagsalita pa, BP 160/100."
        ),
    },
    # ── YELLOW ───────────────────────────────────────────────────────────────
    {
        "id": "Y1", "level": "yellow", "lang": "ha",
        "text": (
            "Mace shekaru 35. Ciwon kai mai tsanani tun safe. "
            "Babu zazzabi, babu amai, hangen neta daidai. "
            "Tana iya tafiya."
        ),
    },
    {
        "id": "Y2", "level": "yellow", "lang": "en",
        "text": (
            "Child 4 years. Fever 38.9C for 2 days, alert, crying. "
            "RR 28, HR 118. Eating less but drinking. No seizures."
        ),
    },
    # ── GREEN ─────────────────────────────────────────────────────────────────
    {
        "id": "G1", "level": "green", "lang": "en",
        "text": (
            "Minor laceration to left forearm from kitchen knife. "
            "Alert and oriented. HR 80, RR 16, BP 120/78. Bleeding controlled."
        ),
    },
    {
        "id": "G2", "level": "green", "lang": "bn",
        "text": (
            "২০ বছরের মেয়ে। গত ৩ দিন ধরে নাক দিয়ে পানি পড়ছে, হালকা কাশি। "
            "জ্বর নেই, শ্বাসকষ্ট নেই। খাওয়া দাওয়া স্বাভাবিক।"
        ),
    },
    # ── BLUE ──────────────────────────────────────────────────────────────────
    {
        "id": "B1", "level": "blue", "lang": "en",
        "text": (
            "Patient brought in by family. No breathing, no pulse, "
            "fixed dilated pupils. Body cold to touch. Rigor mortis present. "
            "Family states found at home several hours ago."
        ),
    },
    {
        "id": "B2", "level": "blue", "lang": "sw",
        "text": (
            "Mzee wa miaka 80 aliyeletwa na familia. Hakuna mapigo ya moyo, "
            "hakuna pumzi. Mwili baridi. Familia inasema alifariki usiku wa jana."
        ),
    },
]

# ===========================================================================
#  ENGINE — do not edit below this line
# ===========================================================================

_LANG_NAMES = {
    "en": "English", "sw": "Swahili", "tl": "Tagalog",
    "ha": "Hausa",   "bn": "Bengali",
}
_LEVELS   = ["red", "orange", "yellow", "green", "blue"]
_COLOURS  = {"red": "\033[91m", "orange": "\033[93m", "yellow": "\033[33m",
             "green": "\033[92m", "blue": "\033[94m"}
_RESET    = "\033[0m"
_BOLD     = "\033[1m"


def _col(level: Optional[str]) -> str:
    if not level:
        return f"\033[90m?{_RESET}"
    return f"{_COLOURS.get(level, '')}{level.upper()}{_RESET}"


def _normalise(raw: str) -> Optional[str]:
    if not raw:
        return None
    r = raw.lower().strip()
    if r in _LEVELS:
        return r
    return None


def _parse(raw: str) -> Optional[str]:
    if "[End thinking]" in raw:
        raw = raw.split("[End thinking]")[-1].strip()
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*",     "", raw)
    start = raw.find("{")
    if start != -1:
        end  = raw.rfind("}") + 1
        js   = raw[start:end] if end > start else raw[start:] + "}"
        js   = re.sub(r",\s*}", "}", js)
        js   = re.sub(r",\s*]", "]", js)
        try:
            result = _normalise(str(json.loads(js).get("triage_level", "")))
            if result:
                return result
        except json.JSONDecodeError:
            pass
    m = re.search(r'"triage_level"\s*:\s*"([^"]+)"', raw, re.IGNORECASE)
    return _normalise(m.group(1)) if m else None


def _parse_full(raw: str) -> Optional[dict]:
    if "[End thinking]" in raw:
        raw = raw.split("[End thinking]")[-1].strip()
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*",     "", raw)
    start = raw.find("{")
    if start == -1:
        return None
    end = raw.rfind("}") + 1
    js  = raw[start:end] if end > start else raw[start:] + "}"
    js  = re.sub(r",\s*}", "}", js)
    js  = re.sub(r",\s*]", "]", js)
    try:
        return json.loads(js)
    except json.JSONDecodeError:
        return None


def run_case(case: dict, verbose: bool, dry_run: bool = False) -> tuple[Optional[str], float, str]:
    predicted, latency, raw_full = run_inference(
        FINE_GGUF, case["text"], case["lang"],
        dry_run=dry_run,
        system_prompt=SYSTEM_PROMPT,
        temp=TEMP, repeat_penalty=REPEAT_PENALTY, max_tokens=MAX_TOKENS,
    )

    if verbose:
        print(f"\n  ┌─ {case['id']}  expected={_col(case['level'])}  {'─'*38}")
        model_start = raw_full.rfind("<start_of_turn>model")
        display_text = raw_full[model_start:] if model_start != -1 else raw_full
        if "[End thinking]" in display_text:
            display_text = display_text.split("[End thinking]")[-1].strip()
        parsed = _parse_full(display_text)
        if parsed:
            print("  │  " + json.dumps(parsed, indent=2).replace("\n", "\n  │  "))
        else:
            print(f"  │  [raw]: {display_text[:500]}")
        mark = "✓" if predicted == case["level"] else "✗"
        print(f"  └─ extracted : {_col(predicted)} {mark}  ({latency:.1f}s)")

    return predicted, latency, raw_full


def main() -> None:
    parser = argparse.ArgumentParser(
        description="VoiceBridge prompt/param tuner — 10 fixed cases"
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print full model response for every case")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip inference, return lang code as predicted level")
    args = parser.parse_args()

    # Preflight checks (skipped in dry-run)
    if not args.dry_run:
        if not Path(LLAMA_CLI).exists():
            print(f"[ERROR] llama-cli not found: {LLAMA_CLI}")
            sys.exit(1)
        if not Path(FINE_GGUF).exists():
            print(f"[ERROR] GGUF not found: {FINE_GGUF}")
            sys.exit(1)

    print(f"\n{_BOLD}{'='*60}{_RESET}")
    print(f"{_BOLD}  VoiceBridge Prompt Tuner{_RESET}")
    print(f"{'='*60}")
    print(f"  Model          : {Path(FINE_GGUF).name}")
    print(f"  temp           : {TEMP}")
    print(f"  repeat_penalty : {REPEAT_PENALTY}")
    print(f"  max_tokens     : {MAX_TOKENS}")
    print(f"  cases          : {len(TEST_CASES)}")
    print(f"{'='*60}\n")

    correct = 0
    safe    = 0
    results = []
    t_start = time.time()

    for case in TEST_CASES:
        if not args.verbose:
            print(f"  {case['id']} (expected {_col(case['level'])}) ...",
                  end=" ", flush=True)

        predicted, latency, _ = run_case(case, args.verbose, args.dry_run)

        is_correct = (predicted == case["level"])
        is_safe    = (
            predicted in _LEVELS and
            _LEVELS.index(predicted) <= _LEVELS.index(case["level"])
        )

        if not args.verbose:
            mark = "✓" if is_correct else "✗"
            print(f"→ {_col(predicted)} {mark}  ({latency:.1f}s)")

        if is_correct: correct += 1
        if is_safe:    safe    += 1
        results.append({
            "id": case["id"], "expected": case["level"],
            "predicted": predicted, "correct": is_correct, "safe": is_safe,
        })

    elapsed = time.time() - t_start

    # ── Results ────────────────────────────────────────────────────────────
    print(f"\n{_BOLD}{'='*60}{_RESET}")
    print(f"{_BOLD}  SCORE BREAKDOWN{_RESET}")
    print(f"{'='*60}")

    for lvl in _LEVELS:
        cases_lvl   = [r for r in results if r["expected"] == lvl]
        n_correct   = sum(1 for r in cases_lvl if r["correct"])
        wrong_preds = [r["predicted"] for r in cases_lvl if not r["correct"]]
        bar  = "█" * n_correct + "░" * (len(cases_lvl) - n_correct)
        note = f"  ← predicted {', '.join(str(p) for p in wrong_preds)}" if wrong_preds else ""
        print(f"  {_col(lvl):<22} {bar}  {n_correct}/{len(cases_lvl)}{note}")

    print(f"{'─'*60}")

    pct        = correct / len(TEST_CASES)
    safe_pct   = safe    / len(TEST_CASES)
    acc_colour = "\033[92m" if pct >= 0.8 else "\033[93m" if pct >= 0.6 else "\033[91m"

    print(f"  {_BOLD}Exact match     : "
          f"{acc_colour}{correct}/{len(TEST_CASES)} ({pct:.0%}){_RESET}")
    print(f"  {_BOLD}Safe escalation : "
        f"{safe}/{len(TEST_CASES)} ({safe_pct:.0%}){_RESET}")
    print(f"  Total time      : {elapsed:.0f}s")
    print(f"{'='*60}")

    # Verdict
    if pct >= 0.8:
        verdict = f"\033[92m✓ GOOD  — {correct}/10. Run full benchmark.{_RESET}"
    elif pct >= 0.6:
        verdict = f"\033[93m~ OK    — {correct}/10. Tweak prompt and retry.{_RESET}"
    else:
        verdict = f"\033[91m✗ POOR  — {correct}/10. Major revision needed.{_RESET}"
    print(f"\n  {_BOLD}{verdict}")
    print()


if __name__ == "__main__":
    main()