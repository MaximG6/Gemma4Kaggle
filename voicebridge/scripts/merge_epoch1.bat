@echo off
call C:\Users\Maxim\anaconda3\condabin\conda.bat activate voicebridge
python scripts/finetune_v2.py --merge-only --adapter-output models/voicebridge-gemma4-triage-adapter-v2/checkpoint-57
