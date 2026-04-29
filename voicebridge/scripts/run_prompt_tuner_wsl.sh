#!/bin/bash
export CUDA_VISIBLE_DEVICES=1
source /home/maxim/miniconda3/etc/profile.d/conda.sh
conda activate voicebridge
export FINE_GGUF="/home/maxim/voicebridge-finetuned-v2-epoch1-q4km.gguf"
cd /mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge
python scripts/prompt_tuner.py
