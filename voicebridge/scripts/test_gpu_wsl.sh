#!/bin/bash
/mnt/c/Users/Maxim/anaconda3/envs/voicebridge/python.exe -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
