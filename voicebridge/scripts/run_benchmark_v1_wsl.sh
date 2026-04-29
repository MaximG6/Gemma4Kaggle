#!/bin/bash
export CUDA_VISIBLE_DEVICES=1
source /home/maxim/miniconda3/etc/profile.d/conda.sh
conda activate voicebridge
cd /mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge

# Run 100-case benchmark on original V1 model (89% scorer)
FINE_GGUF="/home/maxim/voicebridge-finetuned-q4km.gguf" python scripts/compare_models.py --tuned-only --no-resume
