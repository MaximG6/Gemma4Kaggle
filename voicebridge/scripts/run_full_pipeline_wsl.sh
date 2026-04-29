#!/bin/bash
export CUDA_VISIBLE_DEVICES=1
source /home/maxim/miniconda3/etc/profile.d/conda.sh
conda activate voicebridge

MODEL_DIR="/mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge/models/voicebridge-merged-v2"
echo "=== Checking merged model ==="
ls -lh "$MODEL_DIR/model.safetensors"
echo ""

# Remove corrupted partial file
rm -f /home/maxim/voicebridge-finetuned-v2-epoch1-f16.gguf

# Copy model to WSL native filesystem for better mmap support
echo "=== Copying model to WSL native filesystem ==="
cp -r "$MODEL_DIR" /home/maxim/voicebridge-merged-v2-native/
echo "Copy done. Size:"
ls -lh /home/maxim/voicebridge-merged-v2-native/model.safetensors
echo ""

# Convert to F16 GGUF
echo "=== Converting to F16 GGUF ==="
python /home/maxim/llama.cpp/convert_hf_to_gguf.py /home/maxim/voicebridge-merged-v2-native/ --outfile /home/maxim/voicebridge-finetuned-v2-epoch1-f16.gguf --outtype f16
echo "F16 GGUF done. Size:"
ls -lh /home/maxim/voicebridge-finetuned-v2-epoch1-f16.gguf
echo ""

# Quantize to Q4_K_M
echo "=== Quantizing to Q4_K_M ==="
/home/maxim/llama.cpp/build/bin/llama-quantize /home/maxim/voicebridge-finetuned-v2-epoch1-f16.gguf /home/maxim/voicebridge-finetuned-v2-epoch1-q4km.gguf Q4_K_M
echo "Quantization done. Size:"
ls -lh /home/maxim/voicebridge-finetuned-v2-epoch1-q4km.gguf
