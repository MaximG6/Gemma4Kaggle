"""
VoiceBridge GGUF Export + HuggingFace Upload
=============================================
Loads the saved LoRA adapter, exports directly to GGUF Q4_K_M using
Unsloth's built-in exporter (no intermediate fp16 step, less RAM), then
creates a private HuggingFace repo and uploads the GGUF.

Usage (from voicebridge/ repo root, conda env voicebridge active):
    python scripts/export_gguf.py
    python scripts/export_gguf.py --hf-repo YourUsername/your-repo-name
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Disable xet backend before any HuggingFace import
os.environ["HF_HUB_DISABLE_XET"] = "1"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT    = Path(__file__).resolve().parents[1]
_ADAPTER_PATH = _REPO_ROOT / "models" / "voicebridge-gemma4-triage-adapter"
_GGUF_DIR     = Path.home() / "models"
_GGUF_NAME    = "voicebridge"          # Unsloth appends -Q4_K_M.gguf
_HF_REPO      = "OminousDude/voicebridge-gemma4"
_MAX_SEQ      = 2048


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export LoRA adapter to GGUF and upload to HF")
    p.add_argument("--adapter",    default=str(_ADAPTER_PATH), help="Path to saved LoRA adapter")
    p.add_argument("--gguf-dir",   default=str(_GGUF_DIR),     help="Directory to write GGUF file")
    p.add_argument("--gguf-name",  default=_GGUF_NAME,         help="GGUF filename stem (Unsloth appends -Q4_K_M.gguf)")
    p.add_argument("--hf-repo",    default=_HF_REPO,           help="HuggingFace repo id (username/repo-name)")
    p.add_argument("--no-upload",  action="store_true",         help="Skip HuggingFace upload")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    adapter_path = Path(args.adapter)
    gguf_dir     = Path(args.gguf_dir)
    gguf_stem    = str(gguf_dir / args.gguf_name)
    gguf_file    = gguf_dir / f"{args.gguf_name}-Q4_K_M.gguf"

    print("=" * 64, flush=True)
    print("VoiceBridge — GGUF Export + HF Upload", flush=True)
    print("=" * 64, flush=True)
    print(f"  Adapter  : {adapter_path}", flush=True)
    print(f"  GGUF out : {gguf_file}", flush=True)
    print(f"  HF repo  : {args.hf_repo}", flush=True)
    print("=" * 64, flush=True)

    if not adapter_path.exists():
        print(f"[ERROR] Adapter not found at {adapter_path}", file=sys.stderr)
        sys.exit(1)

    gguf_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Load model + adapter ────────────────────────────────────────
    print("\n[1/3] Loading base model + LoRA adapter …", flush=True)
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name     = str(adapter_path),
        max_seq_length = _MAX_SEQ,
        load_in_4bit   = True,
    )
    print("      Model loaded.", flush=True)

    # ── Step 2: Export to GGUF Q4_K_M ───────────────────────────────────────
    print(f"\n[2/3] Exporting to GGUF Q4_K_M → {gguf_file}", flush=True)
    print("      (Unsloth handles merge + quantise in one pass — no fp16 temp file)", flush=True)
    model.save_pretrained_gguf(
        gguf_stem,
        tokenizer,
        quantization_method = "q4_k_m",
    )

    # Unsloth may produce a slightly different filename — find whatever .gguf was created
    if not gguf_file.exists():
        candidates = list(gguf_dir.glob("*.gguf"))
        if not candidates:
            print(f"[ERROR] No GGUF file found in {gguf_dir}", file=sys.stderr)
            sys.exit(1)
        # Pick the most recently modified one
        gguf_file = max(candidates, key=lambda p: p.stat().st_mtime)
        print(f"      (actual GGUF filename: {gguf_file.name})", flush=True)

    size_gb = gguf_file.stat().st_size / (1024 ** 3)
    print(f"      GGUF saved  — {size_gb:.2f} GB", flush=True)

    if args.no_upload:
        print("\n--no-upload set. Done.", flush=True)
        return

    # ── Step 3: Upload to HuggingFace ───────────────────────────────────────
    print(f"\n[3/3] Uploading to HuggingFace: {args.hf_repo} …", flush=True)

    from huggingface_hub import HfApi
    api = HfApi()

    # Create private repo (no-op if it already exists)
    try:
        api.create_repo(
            repo_id  = args.hf_repo,
            repo_type= "model",
            private  = True,
            exist_ok = True,
        )
        print(f"      Repo ready: huggingface.co/{args.hf_repo}", flush=True)
    except Exception as e:
        print(f"[WARN] Could not create repo (may already exist): {e}", flush=True)

    # Upload GGUF file
    api.upload_file(
        path_or_fileobj = str(gguf_file),
        path_in_repo    = gguf_file.name,
        repo_id         = args.hf_repo,
        repo_type       = "model",
    )

    print(f"\n      Uploaded → huggingface.co/{args.hf_repo}/{gguf_file.name}", flush=True)
    print("\n" + "=" * 64, flush=True)
    print("Done. Deploy to Raspberry Pi 5 with:", flush=True)
    print(f"  hf download {args.hf_repo} {gguf_file.name} --local-dir ~/models/", flush=True)
    print("  ./llama.cpp/build/bin/llama-cli \\", flush=True)
    print(f"      -m ~/models/{gguf_file.name} \\", flush=True)
    print("      -n 512 --threads 4", flush=True)
    print("=" * 64, flush=True)


if __name__ == "__main__":
    main()
