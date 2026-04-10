"""
VoiceBridge GGUF Quantisation — Task 4.4
==========================================
Converts the fine-tuned merged model to GGUF Q4_K_M format for
deployment on Raspberry Pi 5 (8 GB) via llama.cpp.

Prerequisites:
  1. llama.cpp must be compiled at ~/llama.cpp:
         git clone https://github.com/ggerganov/llama.cpp ~/llama.cpp
         cmake ~/llama.cpp -B ~/llama.cpp/build -DGGML_NATIVE=OFF
         cmake --build ~/llama.cpp/build --config Release -j $(nproc)
     The scripts used are:
         ~/llama.cpp/convert_hf_to_gguf.py   (Python — needs pip install gguf)
         ~/llama.cpp/build/bin/llama-quantize (compiled binary)
  2. Conda env voicebridge must be active (Python 3.11, transformers, gguf).
  3. models/voicebridge-merged/ must exist (output of finetune.py merge step).

Usage (from voicebridge/ repo root):
    python scripts/quantise.py
    python scripts/quantise.py --merged-path /custom/merged --llama-root ~/llama.cpp

Outputs:
    models/voicebridge-f16.gguf    — intermediate fp16 GGUF
    models/voicebridge-q4km.gguf   — final Q4_K_M for Pi 5
    models/quantise_log.json       — metadata + file sizes
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULT_LLAMA_ROOT   = Path.home() / "llama.cpp"
_DEFAULT_MERGED_PATH  = _REPO_ROOT / "models" / "voicebridge-merged"
_DEFAULT_F16_PATH     = _REPO_ROOT / "models" / "voicebridge-f16.gguf"
_DEFAULT_Q4KM_PATH    = _REPO_ROOT / "models" / "voicebridge-q4km.gguf"
_DEFAULT_LOG_PATH     = _REPO_ROOT / "models" / "quantise_log.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gb(path: Path) -> float:
    """Return file size in GiB (1 GiB = 1024³ bytes)."""
    return path.stat().st_size / (1024 ** 3)


def _run(cmd: list[str]) -> None:
    """Print the command then execute it, raising on non-zero exit."""
    print("\n$ " + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}:\n"
            + " ".join(str(c) for c in cmd)
        )


# ---------------------------------------------------------------------------
# Main quantisation routine
# ---------------------------------------------------------------------------

def quantise(
    merged_path: Path,
    f16_path: Path,
    q4km_path: Path,
    llama_root: Path,
    log_path: Path,
) -> None:
    # ── Validate inputs ───────────────────────────────────────────────────────
    if not merged_path.exists():
        print(
            f"[ERROR] Merged model not found at {merged_path}\n"
            "        Run finetune.py first (without --dry-run) to produce the merged model.",
            file=sys.stderr,
        )
        sys.exit(1)

    convert_script = llama_root / "convert_hf_to_gguf.py"
    if not convert_script.exists():
        print(
            f"[ERROR] llama.cpp convert script not found at {convert_script}\n"
            "        Build llama.cpp at ~/llama.cpp — see the docstring for instructions.",
            file=sys.stderr,
        )
        sys.exit(1)

    quantize_bin = llama_root / "build" / "bin" / "llama-quantize"
    if not quantize_bin.exists():
        # Some builds place the binary directly in build/
        quantize_bin = llama_root / "build" / "llama-quantize"
    if not quantize_bin.exists():
        print(
            f"[ERROR] llama-quantize binary not found under {llama_root}/build\n"
            "        Compile llama.cpp first — see the docstring for instructions.",
            file=sys.stderr,
        )
        sys.exit(1)

    f16_path.parent.mkdir(parents=True, exist_ok=True)
    q4km_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    run_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    t0 = time.time()

    # ── Step 1: HF → fp16 GGUF ───────────────────────────────────────────────
    print("=" * 64)
    print("Step 1 — Convert HuggingFace model to fp16 GGUF")
    print("=" * 64)
    _run([
        sys.executable,
        str(convert_script),
        str(merged_path),
        "--outfile", str(f16_path),
        "--outtype", "f16",
    ])

    if not f16_path.exists():
        raise RuntimeError(f"Expected fp16 GGUF not created at {f16_path}")
    f16_gb = _gb(f16_path)
    print(f"\n  fp16 GGUF created: {f16_path}")
    print(f"  Size: {f16_gb:.2f} GB")

    # ── Step 2: fp16 GGUF → Q4_K_M ───────────────────────────────────────────
    print("\n" + "=" * 64)
    print("Step 2 — Quantise to Q4_K_M")
    print("=" * 64)
    _run([
        str(quantize_bin),
        str(f16_path),
        str(q4km_path),
        "Q4_K_M",
    ])

    if not q4km_path.exists():
        raise RuntimeError(f"Expected Q4_K_M GGUF not created at {q4km_path}")
    q4km_gb = _gb(q4km_path)
    print(f"\n  Q4_K_M GGUF created: {q4km_path}")
    print(f"  Size: {q4km_gb:.2f} GB")

    elapsed = time.time() - t0

    # ── Save quantise log ─────────────────────────────────────────────────────
    log = {
        "source_path":       str(merged_path),
        "f16_output_path":   str(f16_path),
        "output_path":       str(q4km_path),
        "quantisation_type": "Q4_K_M",
        "f16_size_gb":       round(f16_gb,   3),
        "file_size_gb":      round(q4km_gb,  3),
        "compression_ratio": round(f16_gb / q4km_gb, 2) if q4km_gb > 0 else None,
        "llama_root":        str(llama_root),
        "elapsed_s":         round(elapsed, 1),
        "timestamp":         run_timestamp,
    }
    log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"\n  Quantise log saved → {log_path}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 64)
    print("Quantisation Summary")
    print("=" * 64)
    print(f"  Source (merged HF)  : {merged_path}")
    print(f"  fp16 GGUF           : {f16_path}  ({f16_gb:.2f} GB)")
    print(f"  Q4_K_M GGUF         : {q4km_path}  ({q4km_gb:.2f} GB)")
    if q4km_gb > 0:
        print(f"  Compression ratio   : {f16_gb / q4km_gb:.2f}×")
    print(f"  Elapsed             : {elapsed:.0f}s")
    print("=" * 64)
    print(
        "\nDeploy to Raspberry Pi 5 with:\n"
        f"  scp {q4km_path} pi@raspberrypi:~/models/\n"
        "  ./llama.cpp/build/bin/llama-cli \\\n"
        "      -m ~/models/voicebridge-q4km.gguf \\\n"
        "      -p '<start_of_turn>user\\n...<end_of_turn>\\n<start_of_turn>model\\n' \\\n"
        "      -n 512 --threads 4"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert VoiceBridge merged model to GGUF Q4_K_M for Raspberry Pi 5"
    )
    parser.add_argument(
        "--merged-path",
        default=str(_DEFAULT_MERGED_PATH),
        help=f"Path to merged HuggingFace model (default: {_DEFAULT_MERGED_PATH})",
    )
    parser.add_argument(
        "--f16-out",
        default=str(_DEFAULT_F16_PATH),
        help=f"Output path for intermediate fp16 GGUF (default: {_DEFAULT_F16_PATH})",
    )
    parser.add_argument(
        "--q4km-out",
        default=str(_DEFAULT_Q4KM_PATH),
        help=f"Output path for Q4_K_M GGUF (default: {_DEFAULT_Q4KM_PATH})",
    )
    parser.add_argument(
        "--llama-root",
        default=str(_DEFAULT_LLAMA_ROOT),
        help=f"Root directory of llama.cpp checkout (default: {_DEFAULT_LLAMA_ROOT})",
    )
    parser.add_argument(
        "--log-path",
        default=str(_DEFAULT_LOG_PATH),
        help=f"Path for quantise_log.json (default: {_DEFAULT_LOG_PATH})",
    )
    args = parser.parse_args()

    print("=" * 64)
    print("VoiceBridge GGUF Quantisation")
    print("=" * 64)
    print(f"  Source     : {args.merged_path}")
    print(f"  fp16 out   : {args.f16_out}")
    print(f"  Q4_K_M out : {args.q4km_out}")
    print(f"  llama.cpp  : {args.llama_root}")
    print("=" * 64)

    quantise(
        merged_path = Path(args.merged_path),
        f16_path    = Path(args.f16_out),
        q4km_path   = Path(args.q4km_out),
        llama_root  = Path(args.llama_root),
        log_path    = Path(args.log_path),
    )


if __name__ == "__main__":
    main()
