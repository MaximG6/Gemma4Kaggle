#!/bin/bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate voicebridge

# WSL CUDA ordering: CUDA device 0 = 4090 (cc 8.9), CUDA device 1 = 5090 (cc 12.0)
# nvidia-smi ordering: index 0 = 5090, index 1 = 4090
# We want the 4090 → CUDA device 0 → CUDA_VISIBLE_DEVICES=0
export CUDA_VISIBLE_DEVICES=0

echo "=== nvidia-smi ==="
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader

echo "=== Python CUDA check ==="
python -c "
import os
print('CUDA_VISIBLE_DEVICES:', os.environ.get('CUDA_VISIBLE_DEVICES'))
from llama_cpp import llama_supports_gpu_offload, llama_backend_init
llama_backend_init()
print('GPU offload supported:', llama_supports_gpu_offload())
"

echo "=== Running benchmark ==="
python -u /mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge/scripts/compare_models.py --tuned-only --no-resume 2>&1

echo "=== Post-run nvidia-smi ==="
nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader
