# VoiceBridge

Offline multilingual clinical triage AI built on Gemma 4 E4B. A nurse speaks or types a patient intake in any language — VoiceBridge returns a structured SATS triage level with red flag indicators and a recommended action. No internet required.

Built for the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) by Maxim Gerasimov.

**Live demo:** https://voicebridge.octo.net/ui/

---

## What it does

- Takes voice or text patient intake in any language
- Returns a colour-coded SATS triage level (RED / ORANGE / YELLOW / GREEN / BLUE)
- Runs fully offline via llama.cpp — no cloud, no API keys, no recurring cost
- Supports 140 languages natively via Gemma 4's multilingual capability
- Interactive mode asks clarifying questions when intake is incomplete
- Deployable on a Raspberry Pi 5 or Nvidia Jetson Orin Nano

## Results

Benchmarked on 100 real SATS-aligned clinical cases across 5 languages (Swahili, Bengali, English, Hausa, Tagalog):

| Metric | Base Gemma 4 E4B | VoiceBridge Fine-tuned |
|---|---|---|
| Exact match accuracy | 85% | **96%** |
| Safe escalation rate | 89% | **100%** |
| Unsafe under-triage cases | 11 | **0** |
| RED detection | 95% | **100%** |
| BLUE detection | 80% | **100%** |

*Base Gemma 4 E4B uses the same custom prompt as my tuned model, which boosts its scores.*

Zero unsafe under-triage cases. Every miss is a safe over-triage.

## How it works

1. **Fine-tuning** — QLoRA fine-tune of Gemma 4 E4B using Unsloth on 500 SATS/WHO ETAT clinical scenarios across 8 language contexts
2. **Quantisation** — exported to GGUF Q4_K_M via Unsloth's built-in exporter (2.5GB)
3. **Inference** — llama.cpp with full GPU offload on desktop, CPU-only on Pi
4. **Frontend** — Flutter web app with audio recording, text input, and interactive mode
5. **Backend** — FastAPI serving the model via llama-cpp-python

Thinking mode was disabled after feedback from Medic's engineering team — speed and battery life matter more than reasoning depth on edge devices.

## Repo structure

```
voicebridge/
├── api/              FastAPI backend
├── models/           Language detection and transcription
├── pipeline/         Triage inference pipeline
├── voicebridge_app/  Flutter frontend
├── scripts/          Fine-tuning, benchmarking, model export
├── data/             Benchmark cases (100 cases, 5 languages)
└── docs/             Benchmark results
```

## Running locally

**Backend**
```bash
conda create -n voicebridge python=3.11
conda activate voicebridge
pip install -r requirements.txt

# Download model
python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download('OminousDude/voicebridge-gemma4', 'voicebridge-finetuned-q4km.gguf', local_dir='./models')
"

# Start server
PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Test**
```bash
curl -X POST http://localhost:8000/intake/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Child seizing for 8 minutes, unresponsive.", "lang": "en"}'
```

**Frontend**

The pre-built Flutter web app is in `voicebridge_app/build/web/`. Copy it to the `frontend/` directory and it will be served at `/ui/`.

To rebuild from source: `flutter build web --release --base-href "/ui/"`

## Model

- **Base:** Gemma 4 E4B (Apache 2.0)
- **Fine-tune:** QLoRA, rank 32, alpha 64, Unsloth on RTX 5090
- **Training data:** 500 SATS/WHO ETAT clinical examples, 8 language contexts
- **Inference:** llama.cpp Q4_K_M GGUF, 2.5GB
- **HuggingFace:** https://huggingface.co/OminousDude/voicebridge-gemma4

## Real-world validation

Medic (medic.org), stewards of the Community Health Toolkit deployed to 100,000+ health workers across 15+ countries, reached out after seeing VoiceBridge. Their team expressed interest in building an Android APK connecting to CHT via VoiceBridge's structured JSON output and asked us to prioritise Swahili and Bengali.

## Benchmark Methodology

The 100-case benchmark dataset was curated from SATS 2023 and WHO ETAT 
clinical scenarios. English source cases were translated into Swahili, 
Bengali, Hausa, and Tagalog for multilingual evaluation. Labels are the 
expected SATS triage level based on clinical discriminators and vital sign 
thresholds defined in the SATS 2023 specification. All inference was run 
via llama.cpp on an RTX 5090 with full GPU offload (-ngl 99). Benchmark 
script is at voicebridge/scripts/compare_models.py. Results are logged 
to voicebridge/docs/final_benchmark.json.

## License

Apache 2.0
