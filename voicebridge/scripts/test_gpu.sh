#!/bin/bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate voicebridge
cd /mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
