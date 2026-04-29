# Requires PowerShell execution
& C:\Users\Maxim\anaconda3\shell\condabin\conda-hook.ps1
conda activate voicebridge
python scripts/finetune_v2.py --merge-only --adapter-output models/voicebridge-gemma4-triage-adapter-v2/checkpoint-57
