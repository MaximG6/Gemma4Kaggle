#!/bin/bash
source /home/maxim/miniconda3/etc/profile.d/conda.sh
conda activate voicebridge
cd /mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge
python scripts/generate_charts.py --input docs/model_comparison.json --output docs/benchmark_charts.png
