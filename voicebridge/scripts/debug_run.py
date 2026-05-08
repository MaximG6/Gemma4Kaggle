#!/usr/bin/env python
import os, sys, traceback

# Set GPU BEFORE any imports
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.putenv("CUDA_VISIBLE_DEVICES", "0")

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _REPO_ROOT)

print("=== Debug Info ===", flush=True)
print(f"CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES')}", flush=True)
print(f"Python: {sys.executable}", flush=True)
print(f"Platform: {sys.platform}", flush=True)
print(f"Working dir: {os.getcwd()}", flush=True)

try:
    import llama_cpp
    print(f"llama_cpp version: {llama_cpp.__version__}", flush=True)
    print(f"llama_cpp location: {llama_cpp.__file__}", flush=True)
except Exception as e:
    print(f"llama_cpp import failed: {e}", flush=True)

try:
    from pipeline.llama_infer import run_inference, FINE_GGUF
    print(f"Model path: {FINE_GGUF}", flush=True)
    print(f"CVD after import: {os.environ.get('CUDA_VISIBLE_DEVICES')}", flush=True)
    
    # Test single inference
    print("\n=== Running single test case ===", flush=True)
    result = run_inference(
        FINE_GGUF,
        "Patient reports severe chest pain radiating to left arm, shortness of breath",
        "en",
        False
    )
    predicted, latency, raw = result
    print(f"Predicted: {predicted}", flush=True)
    print(f"Latency: {latency:.2f}s", flush=True)
    print(f"Raw (first 200 chars): {raw[:200]}", flush=True)
    print("\n=== SUCCESS ===", flush=True)
except Exception as e:
    print(f"\n=== ERROR ===", flush=True)
    traceback.print_exc()
    sys.exit(1)
