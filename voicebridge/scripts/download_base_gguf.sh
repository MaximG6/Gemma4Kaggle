#!/usr/bin/env bash
# Download Gemma 4 E4B Q4_K_M GGUF (base model, no fine-tuning)
# from Unsloth's HuggingFace repo for baseline comparison on Pi 5.

set -e

DEST="${1:-$HOME/models}"
mkdir -p "$DEST"

echo "Downloading Gemma 4 E4B Q4_K_M → $DEST"

hf download unsloth/gemma-4-e4b-it-GGUF \
  gemma-4-E4B-it-Q4_K_M.gguf \
  --local-dir "$DEST"

echo "Done: $DEST/gemma-4-e4b-it-Q4_K_M.gguf"
echo "Size: $(du -h "$DEST/gemma-4-e4b-it-Q4_K_M.gguf" | cut -f1)"
