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
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

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
MAX_TOKENS     = 512    # max output length. try 300, 512, 600
GPU_LAYERS     = 99     # keep at 99 for RTX 5090
THREADS        = 4

# ── System prompt ─────────────────────────────────────────────────────────────
# This is the main thing to experiment with.
# Current version: detailed with few-shot examples and explicit red criteria.
#
# To test a different prompt:
#   1. Comment out SYSTEM_PROMPT below
#   2. Uncomment one of the ALTERNATIVE prompts further down
#   3. Run and compare scores

SYSTEM_PROMPT = """\
You are a clinical triage assistant trained on SATS 2023 and WHO ETAT guidelines.
The nurse's report language: {lang_name}.
Extract structured triage data from the intake report.

You MUST respond with ONLY a single JSON object. No markdown, no code fences, no explanation.
The JSON MUST use EXACTLY these field names:
  triage_level        — REQUIRED. Must be exactly one of: red, orange, yellow, green, blue
  primary_complaint   — REQUIRED. One sentence describing the main clinical problem
  red_flag_indicators — REQUIRED. Array of strings listing clinical red flags present
  recommended_action  — REQUIRED. Specific clinical action to take immediately
  confidence_score    — REQUIRED. Number between 0.0 and 1.0

Triage level definitions:
  red    = immediately life-threatening (cardiac arrest, active seizure >5min, uncontrolled haemorrhagic shock, AVPU=U, eclampsia)
  orange = very urgent but STABLE — see within 10 minutes (suspected MI with normal BP, stroke alert, high fever with altered consciousness)
  yellow = urgent — see within 1 hour (moderate pain, stable fever in child, minor head injury, vomiting blood if stable)
  green  = standard queue — see within 4 hours (minor wounds, sore throat, mild fever, routine)
  blue   = deceased or expectant (unsurvivable without major resources)

CRITICAL RULE — Only assign "red" if the patient has at least ONE of:
  - Absent or agonal breathing / no palpable pulse
  - Active generalised seizure lasting >5 minutes or AVPU=U
  - Uncontrolled haemorrhage WITH shock signs (HR>140 AND SBP<80)
  - SpO2 <85% or RR <8 or RR >38 in an adult
  - Active eclampsia (seizure in pregnancy)
If none of these are present, use "orange" for serious presentations, not "red".

Few-shot examples:

Input: "Child 2 years. Convulsing for 10 minutes. Unresponsive. High fever."
Output: {{"triage_level": "red", "primary_complaint": "Status epilepticus in a febrile toddler", "red_flag_indicators": ["active seizure >5 min", "AVPU=U"], "recommended_action": "Immediate airway protection, IV/IO benzodiazepine, measure glucose, prepare cooling.", "confidence_score": 0.98}}

Input: "Adult male. Chest pain 45 min, radiates left arm. HR 108, BP 138/85, alert, sweating."
Output: {{"triage_level": "orange", "primary_complaint": "Suspected acute coronary syndrome, haemodynamically stable", "red_flag_indicators": ["chest pain with radiation", "tachycardia", "diaphoresis"], "recommended_action": "ECG immediately, aspirin 300mg, IV access, cardiac monitoring, call cardiology.", "confidence_score": 0.93}}

Input: "Child 4 years. Fever 38.9C for 2 days. Alert, eating. RR 28, HR 118."
Output: {{"triage_level": "yellow", "primary_complaint": "Febrile child with mild tachycardia, haemodynamically stable", "red_flag_indicators": ["fever in child", "tachycardia"], "recommended_action": "Full assessment within 1 hour, antipyretic, oral fluids, monitor RR.", "confidence_score": 0.88}}

Input: "Adult. Sore throat 2 days, low-grade fever 37.8C, eating normally, alert."
Output: {{"triage_level": "green", "primary_complaint": "Mild upper respiratory tract infection", "red_flag_indicators": [], "recommended_action": "Standard queue. Symptomatic treatment. Return if worsens.", "confidence_score": 0.94}}

Input: "Patient. No breathing, no pulse, fixed dilated pupils. Cold body, rigor mortis."
Output: {{"triage_level": "blue", "primary_complaint": "Confirmed death — rigor mortis and absent vital signs", "red_flag_indicators": ["no respirations", "no pulse", "fixed dilated pupils", "rigor mortis"], "recommended_action": "Do not resuscitate. Notify next of kin. Handle respectfully.", "confidence_score": 0.99}}

Now process the following intake report:\
"""

# ── ALTERNATIVE A — Minimal prompt, no examples ──────────────────────────────
# SYSTEM_PROMPT = """\
# You are a SATS 2023 clinical triage assistant. Language: {lang_name}.
# Output ONLY a JSON object with fields:
#   triage_level (must be: red/orange/yellow/green/blue)
#   primary_complaint, red_flag_indicators, recommended_action, confidence_score
# red=life-threatening now, orange=urgent stable 10min,
# yellow=1hr, green=4hr, blue=deceased\
# """

# ── ALTERNATIVE B — Strict, no examples, explicit negative constraints ────────
# SYSTEM_PROMPT = """\
# Clinical triage assistant. SATS 2023. Language: {lang_name}.
# Output: ONE JSON object only. No other text.
# Required fields: triage_level, primary_complaint, red_flag_indicators, recommended_action, confidence_score
# triage_level rules:
#   blue  = confirmed death (rigor, fixed pupils, cold)
#   red   = arrest OR active seizure >5min OR AVPU=U OR SpO2<85
#   orange = serious but breathing and responding (chest pain, stroke, sepsis)
#   yellow = moderate urgency, stable vitals
#   green  = minor, can wait hours\
# """

# ── ALTERNATIVE C — Chain-of-thought then JSON ────────────────────────────────
# SYSTEM_PROMPT = """\
# You are a clinical triage assistant (SATS 2023). Language: {lang_name}.
# First identify the 3 most critical clinical findings, then output JSON.
# Format: {{
#   "reasoning": "1. finding  2. finding  3. finding",
#   "triage_level": "red|orange|yellow|green|blue",
#   "primary_complaint": "...",
#   "red_flag_indicators": [...],
#   "recommended_action": "...",
#   "confidence_score": 0.0-1.0
# }}\
# """

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
    if any(x in r for x in ("immediate", "critical", "red")):    return "red"
    if any(x in r for x in ("very urgent", "orange")):           return "orange"
    if "urgent" in r and "very" not in r:                        return "yellow"
    if "yellow" in r:                                            return "yellow"
    if any(x in r for x in ("standard", "green")):               return "green"
    if any(x in r for x in ("dead", "deceased", "expectant", "blue")): return "blue"
    for i, lvl in enumerate(_LEVELS, 1):
        if r.strip() == str(i):
            return lvl
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


def _quote(s: str) -> str:
    return "'" + str(s).replace("'", "'\\''") + "'"


def run_case(case: dict, verbose: bool) -> tuple[Optional[str], float, str]:
    lang    = _LANG_NAMES.get(case["lang"], "English")
    system  = SYSTEM_PROMPT.format(lang_name=lang)
    prompt  = (
        f"<start_of_turn>system\n{system}<end_of_turn>\n"
        f"<start_of_turn>user\n{case['text']}<end_of_turn>\n"
        f"<start_of_turn>model\n{{"
    )
    tmp = Path(f"/tmp/vb_tune_{case['id']}_{os.getpid()}.txt")

    cmd = " ".join(_quote(c) for c in [
        LLAMA_CLI, "-m", FINE_GGUF, "-p", prompt,
        "-n", str(MAX_TOKENS), "--threads", str(THREADS),
        "--temp", str(TEMP), "--repeat-penalty", str(REPEAT_PENALTY),
        "-ngl", str(GPU_LAYERS), "--single-turn", "--log-disable",
    ]) + f" > {_quote(str(tmp))} 2>&1"

    t0 = time.time()
    try:
        subprocess.run(cmd, shell=True, stdin=subprocess.DEVNULL,
                       timeout=120, check=False)
    except subprocess.TimeoutExpired:
        tmp.unlink(missing_ok=True)
        return None, 120.0, "[TIMEOUT]"

    latency  = time.time() - t0
    raw_full = tmp.read_text(errors="replace").strip() if tmp.exists() else ""
    tmp.unlink(missing_ok=True)

    raw_full = re.sub(r'\x1b\[[0-9;]*[mGKHFABCDJK]', '', raw_full)
    raw_full = re.sub(r'\r', '', raw_full)
    brace    = raw_full.find("{")
    raw      = raw_full[brace:] if brace != -1 else "{}"

    predicted = _parse(raw)

    if verbose:
        print(f"\n  ┌─ {case['id']}  expected={_col(case['level'])}  {'─'*38}")
        parsed = _parse_full(raw)
        if parsed:
            print("  │  " + json.dumps(parsed, indent=2).replace("\n", "\n  │  "))
        else:
            print(f"  │  [raw]: {raw[:500]}")
        mark = "✓" if predicted == case["level"] else "✗"
        print(f"  └─ extracted : {_col(predicted)} {mark}  ({latency:.1f}s)")

    return predicted, latency, raw


def main() -> None:
    parser = argparse.ArgumentParser(
        description="VoiceBridge prompt/param tuner — 10 fixed cases"
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print full model response for every case")
    args = parser.parse_args()

    # Preflight checks
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

        predicted, latency, _ = run_case(case, args.verbose)

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
          f"{correct}/{len(TEST_CASES)} ({safe_pct:.0%}){_RESET}")
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