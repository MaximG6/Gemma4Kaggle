#!/bin/bash
export CUDA_VISIBLE_DEVICES=1
source /home/maxim/miniconda3/etc/profile.d/conda.sh
conda activate voicebridge
cd /mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge
python scripts/finetune_v2.py --merge-only --adapter-output models/voicebridge-gemma4-triage-adapter-v2/checkpoint-57
