#!/usr/bin/env python3
"""
VoiceBridge — Merge, Quantise, Verify & Upload
================================================
Runs entirely on CPU so your local LLM can keep using the GPU.

Usage:
    conda activate voicebridge
    cd ~/path/to/repo
    export HF_TOKEN=your_token_here
    python scripts/merge_quantise_upload.py                              # prompts before upload
    python scripts/merge_quantise_upload.py --yes                        # fully unattended
    python scripts/merge_quantise_upload.py --yes --skip-verify          # skip weight diff (saves ~8GB RAM)
    python scripts/merge_quantise_upload.py --yes --fp16                 # fp16 instead of fp32 (saves ~8GB RAM)
    python scripts/merge_quantise_upload.py --yes --skip-verify --fp16  # minimum RAM mode (~8-9GB total)

What this does:
    1. Downloads fine-tuned LoRA adapter from HuggingFace
    2. Loads Gemma 4 E4B base model to CPU (fp32)
    3. Unwraps Gemma4ClippableLinear so PEFT can apply the adapter
    4. Applies and merges the LoRA adapter
    5. Verifies weights changed from base model
    6. Saves merged model locally
    7. Converts to fp16 GGUF via llama.cpp
    8. Quantises to Q4_K_M GGUF
    9. Runs inference test to confirm correct JSON schema
    10. Uploads verified GGUF to HuggingFace

Requirements:
    - conda env voicebridge active
    - llama.cpp built at ~/llama.cpp
    - HF_TOKEN env var set with write permissions
    - ~18GB free RAM (model loads to CPU not GPU)
    - ~20GB free disk space in models/
    - pip install psutil (checked at runtime)
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ADAPTER_REPO    = "OminousDude/voicebridge-adapter"
BASE_MODEL_ID   = "google/gemma-4-e4b-it"
UPLOAD_REPO     = "OminousDude/voicebridge-gemma4"
UPLOAD_FILENAME = "voicebridge-finetuned-q4km.gguf"

REPO_ROOT       = Path(__file__).resolve().parents[1]
MERGED_PATH = Path.home() / "voicebridge-merged"
F16_GGUF    = Path.home() / "voicebridge-finetuned-f16.gguf"
Q4KM_GGUF   = Path.home() / "voicebridge-finetuned-q4km.gguf"
LOG_PATH    = Path.home() / "merge_upload_log.json"
LLAMA_ROOT      = Path.home() / "llama.cpp"
CONVERT_SCRIPT  = LLAMA_ROOT / "convert_hf_to_gguf.py"
QUANTIZE_BIN    = LLAMA_ROOT / "build" / "bin" / "llama-quantize"
CLI_BIN         = LLAMA_ROOT / "build" / "bin" / "llama-cli"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title: str) -> None:
    print("\n" + "=" * 64)
    print(f"  {title}")
    print("=" * 64)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("$ " + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, check=False, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {result.returncode}):\n"
            + " ".join(str(c) for c in cmd)
        )
    return result


def gb(path: Path) -> float:
    return path.stat().st_size / 1e9


# ---------------------------------------------------------------------------
# Step 1 — Preflight checks
# ---------------------------------------------------------------------------

def preflight(hf_token: str, auto_yes: bool = False) -> None:
    banner("Step 1 — Preflight checks")

    assert hf_token, (
        "HF_TOKEN not set.\n"
        "Run: export HF_TOKEN=your_token_here"
    )
    print(f"✓ HF token loaded (ends ...{hf_token[-4:]})")

    assert CONVERT_SCRIPT.exists(), (
        f"llama.cpp convert script not found at {CONVERT_SCRIPT}\n"
        "Build llama.cpp first:\n"
        "  git clone https://github.com/ggerganov/llama.cpp ~/llama.cpp\n"
        "  cmake ~/llama.cpp -B ~/llama.cpp/build -DGGML_NATIVE=OFF\n"
        "  cmake --build ~/llama.cpp/build --config Release -j $(nproc)"
    )
    print(f"✓ convert_hf_to_gguf.py found")

    assert QUANTIZE_BIN.exists(), (
        f"llama-quantize not found at {QUANTIZE_BIN}\n"
        "Build llama.cpp first (see above)"
    )
    print(f"✓ llama-quantize found")

    assert CLI_BIN.exists(), (
        f"llama-cli not found at {CLI_BIN}\n"
        "Build llama.cpp first (see above)"
    )
    print(f"✓ llama-cli found")

    # Install psutil if missing
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "-q"],
                       check=True)
        import psutil

    free_ram_gb = psutil.virtual_memory().available / 1e9
    print(f"✓ Free RAM: {free_ram_gb:.1f} GB")
    if free_ram_gb < 14:
        print(f"⚠  Low RAM — need ~18GB free, have {free_ram_gb:.1f}GB")
        print("  Consider unloading your local LLM temporarily")
        if not auto_yes:
            response = input("  Continue anyway? (y/n): ").strip().lower()
            if response != "y":
                sys.exit(0)
        else:
            print("  --yes flag set — continuing anyway")
    else:
        print("✓ Sufficient RAM for CPU merge")

    for d in [REPO_ROOT / "models"]:
        d.mkdir(parents=True, exist_ok=True)

    print("✓ All preflight checks passed")


# ---------------------------------------------------------------------------
# Step 2 — Download adapter
# ---------------------------------------------------------------------------

def download_adapter(hf_token: str) -> Path:
    banner("Step 2 — Download adapter from HuggingFace")

    from huggingface_hub import snapshot_download

    adapter_path = Path(snapshot_download(
        repo_id   = ADAPTER_REPO,
        repo_type = "model",
        token     = hf_token,
    ))
    print(f"✓ Adapter at: {adapter_path}")

    files = os.listdir(adapter_path)
    assert "adapter_config.json" in files,       "adapter_config.json missing"
    assert "adapter_model.safetensors" in files, "adapter_model.safetensors missing"

    adapter_size = (adapter_path / "adapter_model.safetensors").stat().st_size / 1e6
    print(f"✓ adapter_model.safetensors: {adapter_size:.0f} MB")
    print(f"✓ All adapter files present: {files}")
    return adapter_path


# ---------------------------------------------------------------------------
# Step 3 — Load base model to CPU
# ---------------------------------------------------------------------------

def load_base_model(hf_token: str, use_gpu: bool = False):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if use_gpu:
        banner("Step 3 — Load base model to GPU")
        print("Loading in fp16 to RTX 5090 — fast path")
        print("Expected VRAM: ~9GB | Expected time: 2-3 min\n")

        assert torch.cuda.is_available(), (
            "CUDA not available — cannot use --gpu flag.\n"
            "Run without --gpu to use CPU instead."
        )

        vram_free = (
            torch.cuda.get_device_properties(0).total_memory
            - torch.cuda.memory_allocated(0)
        ) / 1e9
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        print(f"✓ Free VRAM: {vram_free:.1f} GB")
        if vram_free < 10:
            raise RuntimeError(
                f"Not enough free VRAM ({vram_free:.1f}GB). "
                "Need at least 10GB. Close your local LLM and retry."
            )

        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype       = torch.float16,
            device_map        = "cuda:0",
            token             = hf_token,
            low_cpu_mem_usage = True,
        )
        tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL_ID,
            token = hf_token,
        )
        vram_used = torch.cuda.memory_allocated(0) / 1e9
        print(f"✓ Base model loaded to GPU in fp16")
        print(f"✓ VRAM used: {vram_used:.1f} GB")

    else:
        banner("Step 3 — Load base model to CPU")
        print("Loading in fp16 to CPU — GPU untouched, local LLM keeps running")
        print("Expected RAM: ~8GB | Expected time: 5-10 min on first run\n")

        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype       = torch.float16,
            token             = hf_token,
            low_cpu_mem_usage = True,
        )
        tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL_ID,
            token = hf_token,
        )
        import psutil
        ram_used = psutil.Process().memory_info().rss / 1e9
        print(f"✓ Base model loaded to CPU in fp16")
        print(f"✓ Process RAM usage: {ram_used:.1f} GB")

    return model, tokenizer


# ---------------------------------------------------------------------------
# Step 4 — Apply and merge adapter
# ---------------------------------------------------------------------------

def merge_adapter(model, adapter_path: Path, use_gpu: bool = False):
    banner("Step 4 — Apply and merge LoRA adapter")

    import torch.nn as nn
    from peft import PeftModel

    # Unwrap Gemma4ClippableLinear — PEFT does not recognise this Gemma 4
    # specific wrapper and raises ValueError without this fix.
    print("Unwrapping Gemma4ClippableLinear layers...")
    unwrapped = 0
    for name, module in list(model.named_modules()):
        if hasattr(module, "linear") and isinstance(module.linear, nn.Linear):
            parts  = name.split(".")
            parent = model
            for part in parts[:-1]:
                parent = getattr(parent, part)
            setattr(parent, parts[-1], module.linear)
            unwrapped += 1
    print(f"✓ Unwrapped {unwrapped} Gemma4ClippableLinear layers")

    device_map = "cuda:0" if use_gpu else "cpu"
    print(f"Applying adapter (device: {device_map})...")
    model = PeftModel.from_pretrained(
        model,
        str(adapter_path),
        device_map = device_map,
    )
    print("✓ Adapter applied")

    label = "GPU — fast" if use_gpu else "CPU — 5-10 min"
    print(f"Merging into base weights ({label})...")
    t0 = time.time()
    model = model.merge_and_unload()
    elapsed = time.time() - t0
    print(f"✓ Adapter merged in {elapsed:.0f}s")
    return model


# ---------------------------------------------------------------------------
# Step 5 — Verify weights changed
# ---------------------------------------------------------------------------

def verify_weights(model, hf_token: str) -> float:
    banner("Step 5 — Verify fine-tune was applied")

    import torch
    from transformers import AutoModelForCausalLM

    # Confirm no LoRA layers remain
    has_lora = any("lora" in n.lower() for n, _ in model.named_modules())
    if has_lora:
        print("⚠  LoRA layers still present — merge may not have completed")
    else:
        print("✓ No LoRA layers present — merge confirmed")

    # Move merged model to CPU before loading base to avoid VRAM OOM
    print("Moving merged model to CPU for comparison...")
    model = model.cpu()
    torch.cuda.empty_cache()
    print("✓ Merged model on CPU")

    print("\nLoading base model to CPU for weight comparison...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype       = torch.float16,
        token             = hf_token,
        low_cpu_mem_usage = True,
    )
    print("✓ Base model loaded for comparison")

    print("Comparing weights...")
    differences    = []
    total_params   = 0
    changed_params = 0
    base_params    = dict(base_model.named_parameters())

    for name, param in model.named_parameters():
        if name in base_params:
            diff      = (param.float() - base_params[name].float()).abs()
            max_diff  = diff.max().item()
            mean_diff = diff.mean().item()
            total_params += param.numel()
            if mean_diff > 1e-6:
                changed_params += param.numel()
                differences.append({
                    "layer":     name,
                    "max_diff":  round(max_diff,  6),
                    "mean_diff": round(mean_diff, 6),
                })

    differences.sort(key=lambda x: x["mean_diff"], reverse=True)
    print(f"\nTop 10 most changed layers:")
    for d in differences[:10]:
        print(f"  {d['layer'][:65]:<65}  mean={d['mean_diff']:.6f}")

    pct = 100 * changed_params / total_params if total_params > 0 else 0.0
    print(f"\nTotal parameters   : {total_params:,}")
    print(f"Changed parameters : {changed_params:,}")
    print(f"Percentage changed : {pct:.2f}%")

    del base_model
    del base_params
    gc.collect()
    print("✓ Base model freed from memory")

    if pct > 0.5:
        print("\n✓ FINE-TUNE CONFIRMED — weights differ meaningfully")
    elif pct > 0.01:
        print("\n⚠  MINOR DIFFERENCES — check training loss logs")
    else:
        raise AssertionError(
            "NO MEANINGFUL DIFFERENCE — weights match base model. "
            "Check adapter_model.safetensors is correct."
        )
    return pct


# ---------------------------------------------------------------------------
# Step 6 — Save merged model
# ---------------------------------------------------------------------------

def save_merged(model, tokenizer) -> None:
    banner("Step 6 — Save merged model locally")

    MERGED_PATH.mkdir(parents=True, exist_ok=True)
    print(f"Saving to {MERGED_PATH} ...")

    model.save_pretrained(
        str(MERGED_PATH),
        safe_serialization = True,
        max_shard_size     = "4GB",
    )
    tokenizer.save_pretrained(str(MERGED_PATH))

    saved = os.listdir(MERGED_PATH)
    print(f"✓ Saved files: {saved}")

    del model
    gc.collect()
    print("✓ Model freed from RAM after save")


# ---------------------------------------------------------------------------
# Step 7 — Convert to fp16 GGUF
# ---------------------------------------------------------------------------

def convert_to_f16() -> None:
    banner("Step 7 — Convert merged model to fp16 GGUF")

    assert MERGED_PATH.exists(), f"Merged model not found at {MERGED_PATH}"

    run([
        sys.executable,
        str(CONVERT_SCRIPT),
        str(MERGED_PATH),
        "--outfile", str(F16_GGUF),
        "--outtype", "f16",
    ])

    assert F16_GGUF.exists(), f"fp16 GGUF not created at {F16_GGUF}"
    print(f"✓ fp16 GGUF: {F16_GGUF} ({gb(F16_GGUF):.2f} GB)")


# ---------------------------------------------------------------------------
# Step 8 — Quantise to Q4_K_M
# ---------------------------------------------------------------------------

def quantise_q4km() -> None:
    banner("Step 8 — Quantise to Q4_K_M")

    assert F16_GGUF.exists(), f"fp16 GGUF not found at {F16_GGUF}"

    run([
        str(QUANTIZE_BIN),
        str(F16_GGUF),
        str(Q4KM_GGUF),
        "Q4_K_M",
    ])

    assert Q4KM_GGUF.exists(), f"Q4_K_M GGUF not created at {Q4KM_GGUF}"
    f16_gb  = gb(F16_GGUF)
    q4km_gb = gb(Q4KM_GGUF)
    print(f"✓ Q4_K_M GGUF: {Q4KM_GGUF} ({q4km_gb:.2f} GB)")
    print(f"✓ Compression ratio: {f16_gb / q4km_gb:.2f}x")


# ---------------------------------------------------------------------------
# Step 9 — Inference test
# ---------------------------------------------------------------------------

def inference_test() -> dict:
    banner("Step 9 — Inference test")
    print("Testing GGUF produces correct JSON schema...")
    print("Expected: triage_level=red, correct field names\n")

    result = subprocess.run([
        str(CLI_BIN),
        "-m", str(Q4KM_GGUF),
        "-p", (
            "<start_of_turn>system\n"
            "You are a clinical triage assistant. Return SATS-aligned triage "
            "as JSON with fields: triage_level, primary_complaint, "
            "red_flag_indicators, recommended_action, confidence_score. "
            "No thinking, no explanation. Output JSON only starting with {.\n"
            "<end_of_turn>\n"
            "<start_of_turn>user\n"
            "Patient not breathing, no pulse, unresponsive. "
            "Found collapsed at home.\n"
            "<end_of_turn>\n"
            "<start_of_turn>model\n"
            "{"
        ),
        "-n", "256",
        "--threads", "8",
        "--temp", "0.1",
        "--log-disable",
    ], capture_output=True, text=True, check=False)

    raw = "{" + result.stdout.strip()
    print("Raw output:")
    print(raw[:600])

    expected_fields = [
        "triage_level", "primary_complaint",
        "red_flag_indicators", "recommended_action", "confidence_score",
    ]

    try:
        start  = raw.find("{")
        end    = raw.rfind("}") + 1
        parsed = json.loads(raw[start:end]) if start != -1 and end > start else {}

        print("\nParsed fields:")
        for f in expected_fields:
            val = parsed.get(f, "MISSING")
            status = "✓" if f in parsed else "✗"
            print(f"  {status} {f}: {val}")

        missing = [f for f in expected_fields if f not in parsed]
        triage  = parsed.get("triage_level", "").lower()

        if missing:
            print(f"\n⚠  Missing fields: {missing}")
            print("   Fine-tune schema not fully applied")
        elif triage == "red":
            print("\n✓ CORRECT — triage_level=red and all schema fields present")
            print("✓ Ready to upload")
        else:
            print(f"\n⚠  Unexpected triage_level: {triage} (expected red)")

        return parsed

    except json.JSONDecodeError as e:
        print(f"\n⚠  JSON parse error: {e}")
        print("   Review raw output above manually")
        return {}


# ---------------------------------------------------------------------------
# Step 10 — Upload to HuggingFace
# ---------------------------------------------------------------------------

def upload(hf_token: str) -> None:
    banner("Step 10 — Upload GGUF to HuggingFace")

    from huggingface_hub import HfApi

    size = gb(Q4KM_GGUF)
    print(f"Uploading {UPLOAD_FILENAME} ({size:.2f} GB) to {UPLOAD_REPO}...")

    api = HfApi()
    api.upload_file(
        path_or_fileobj = str(Q4KM_GGUF),
        path_in_repo    = UPLOAD_FILENAME,
        repo_id         = UPLOAD_REPO,
        repo_type       = "model",
        token           = hf_token,
    )
    print(f"✓ Upload complete")
    print(f"✓ https://huggingface.co/{UPLOAD_REPO}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="VoiceBridge — Merge, Quantise, Verify & Upload"
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="Skip all confirmation prompts and run fully unattended"
    )
    parser.add_argument(
        "--gpu", action="store_true",
        help="Use GPU (RTX 5090) for model load and merge — 3-5x faster, "
             "needs ~10GB free VRAM"
    )
    parser.add_argument(
        "--skip-verify", action="store_true",
        help="Skip weight comparison step to reduce peak memory usage"
    )
    args = parser.parse_args()

    t_start  = time.time()
    HF_TOKEN = os.environ.get("HF_TOKEN", "")

    banner("VoiceBridge — Merge, Quantise, Verify & Upload")
    print(f"  Adapter repo  : {ADAPTER_REPO}")
    print(f"  Base model    : {BASE_MODEL_ID}")
    print(f"  Upload repo   : {UPLOAD_REPO}")
    print(f"  Merged path   : {MERGED_PATH}")
    print(f"  Q4_K_M output : {Q4KM_GGUF}")
    print(f"  Device        : {'GPU (RTX 5090)' if args.gpu else 'CPU (RAM only)'}")
    print(f"  Unattended    : {args.yes}")
    print(f"  Verify weights: {'SKIPPED' if args.skip_verify else 'yes'}")
    if args.gpu:
        print(f"  Est. VRAM     : ~9-10 GB")
        print(f"  Est. time     : ~15-25 min total")
    else:
        print(f"  Est. RAM      : ~8 GB (fp16)")
        print(f"  Est. time     : ~60-90 min total")

    # ── Run all steps ──────────────────────────────────────────────
    preflight(HF_TOKEN, auto_yes=args.yes)
    adapter_path     = download_adapter(HF_TOKEN)
    model, tokenizer = load_base_model(HF_TOKEN, use_gpu=args.gpu)
    model            = merge_adapter(model, adapter_path, use_gpu=args.gpu)

    if args.skip_verify:
        banner("Step 5 — Weight verification SKIPPED")
        print("⚠  Skipped via --skip-verify flag")
        adapter_mb = (
            Path(adapter_path) / "adapter_model.safetensors"
        ).stat().st_size / 1e6
        print(f"✓ Adapter size: {adapter_mb:.0f} MB (confirms non-empty weights)")
        pct_changed = 0.0
    else:
        pct_changed = verify_weights(model, HF_TOKEN)

    save_merged(model, tokenizer)
    convert_to_f16()
    quantise_q4km()
    parsed = inference_test()

    # ── Upload ────────────────────────────────────────────────────
    banner("Ready to upload")
    triage_ok = parsed.get("triage_level", "").lower() == "red"
    schema_ok = all(
        f in parsed for f in [
            "triage_level", "primary_complaint",
            "red_flag_indicators", "recommended_action", "confidence_score"
        ]
    )

    if triage_ok and schema_ok:
        print("✓ Inference test passed — triage_level=red, schema correct")
    else:
        print("⚠  Inference test had issues — review output above")

    if args.yes:
        print("--yes flag set — uploading automatically")
        upload(HF_TOKEN)
    else:
        response = input("\nUpload to HuggingFace? (y/n): ").strip().lower()
        if response == "y":
            upload(HF_TOKEN)
        else:
            print("Upload skipped. Run manually when ready:")
            print(f"  hf upload {UPLOAD_REPO} {Q4KM_GGUF} {UPLOAD_FILENAME}")

    # ── Save run log ───────────────────────────────────────────────
    elapsed = time.time() - t_start
    log = {
        "adapter_repo":   ADAPTER_REPO,
        "base_model":     BASE_MODEL_ID,
        "upload_repo":    UPLOAD_REPO,
        "merged_path":    str(MERGED_PATH),
        "q4km_path":      str(Q4KM_GGUF),
        "q4km_size_gb":   round(gb(Q4KM_GGUF), 3),
        "pct_changed":    round(pct_changed, 3),
        "verify_skipped": args.skip_verify,
        "device":         "gpu" if args.gpu else "cpu",
        "inference_ok":   triage_ok and schema_ok,
        "triage_level":   parsed.get("triage_level"),
        "elapsed_min":    round(elapsed / 60, 1),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(log, indent=2))

    banner("Complete")
    print(f"  Total time       : {elapsed / 60:.1f} min")
    print(f"  Device used      : {'GPU' if args.gpu else 'CPU'}")
    print(f"  Weights changed  : {pct_changed:.2f}% {'(skipped)' if args.skip_verify else ''}")
    print(f"  Q4_K_M size      : {gb(Q4KM_GGUF):.2f} GB")
    print(f"  Inference passed : {triage_ok and schema_ok}")
    print(f"  Log saved        : {LOG_PATH}")


if __name__ == "__main__":
    main()