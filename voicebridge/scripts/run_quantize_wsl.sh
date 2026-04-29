#!/bin/bash
source /home/maxim/miniconda3/etc/profile.d/conda.sh
conda activate voicebridge

# Convert to F16 GGUF
python /home/maxim/llama.cpp/convert_hf_to_gguf.py /mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge/models/voicebridge-merged-v2/ --outfile /home/maxim/voicebridge-finetuned-v2-epoch1-f16.gguf --outtype f16

# Quantize to Q4_K_M
/home/maxim/llama.cpp/build/bin/llama-quantize /home/maxim/voicebridge-finetuned-v2-epoch1-f16.gguf /home/maxim/voicebridge-finetuned-v2-epoch1-q4km.gguf Q4_K_M

echo "=== QUANTIZATION DONE ==="
ls -lh /home/maxim/voicebridge-finetuned-v2-epoch1-q4km.gguf
