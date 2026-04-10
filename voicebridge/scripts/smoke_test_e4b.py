"""
Smoke-test Gemma 4 E4B after download.

Passes 1 second of silent audio and checks that the model produces
a non-empty decoded string without raising. Exits 0 on success, 1 on failure.

Usage (from repo root, conda env voicebridge active):
    python scripts/smoke_test_e4b.py
"""

import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoProcessor, Gemma4ForConditionalGeneration

MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "gemma4-e4b-it"


def main() -> int:
    if not MODEL_DIR.exists():
        print(f"[FAIL] Model directory not found: {MODEL_DIR}")
        print("       Run:  python scripts/download_models.py --e4b")
        return 1

    print(f"Loading processor from {MODEL_DIR} ...")
    processor = AutoProcessor.from_pretrained(str(MODEL_DIR))

    print("Loading model (bfloat16, device_map=auto) ...")
    model = Gemma4ForConditionalGeneration.from_pretrained(
        str(MODEL_DIR),
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    model.eval()

    # 1 second of silence at 16 kHz — the minimal valid input
    dummy_audio = np.zeros(16000, dtype=np.float32)

    inputs = processor(
        audio=dummy_audio,
        sampling_rate=16000,
        text="Transcribe this audio.",
        return_tensors="pt",
    ).to("cuda")

    print("Running inference ...")
    with torch.inference_mode():
        out = model.generate(**inputs, max_new_tokens=64)

    decoded = processor.decode(out[0], skip_special_tokens=True)
    print(f"\nModel output:\n  {decoded!r}\n")

    if not decoded.strip():
        print("[FAIL] Model returned empty output.")
        return 1

    print("[PASS] Gemma 4 E4B smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
