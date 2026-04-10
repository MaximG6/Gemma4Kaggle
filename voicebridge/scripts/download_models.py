"""
Download Gemma 4 models from Hugging Face.

Usage (from repo root, conda env voicebridge active):
    python scripts/download_models.py            # download both models
    python scripts/download_models.py --e4b      # edge model only
    python scripts/download_models.py --moe      # 26B MoE only
"""

import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "models"

SKIP_PATTERNS = ["*.msgpack", "*.h5"]

MODELS = {
    "e4b": {
        "repo_id": "google/gemma-4-e4b-it",
        "local_dir": MODELS_DIR / "gemma4-e4b-it",
        "description": "Gemma 4 E4B (edge, Raspberry Pi 5 target)",
    },
    "moe": {
        "repo_id": "google/gemma-4-27b-it",
        "local_dir": MODELS_DIR / "gemma4-27b-moe",
        "description": "Gemma 4 27B MoE (server-side triage classification)",
    },
}


def download(key: str) -> None:
    m = MODELS[key]
    print(f"\n--- Downloading {m['description']} ---")
    print(f"  repo : {m['repo_id']}")
    print(f"  dest : {m['local_dir']}")
    snapshot_download(
        repo_id=m["repo_id"],
        local_dir=str(m["local_dir"]),
        ignore_patterns=SKIP_PATTERNS,
    )
    print(f"  done : {m['local_dir']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download VoiceBridge models")
    parser.add_argument("--e4b", action="store_true", help="Download Gemma 4 E4B only")
    parser.add_argument("--moe", action="store_true", help="Download Gemma 4 27B MoE only")
    args = parser.parse_args()

    if args.e4b:
        download("e4b")
    elif args.moe:
        download("moe")
    else:
        download("e4b")
        download("moe")


if __name__ == "__main__":
    main()
