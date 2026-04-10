# VoiceBridge

**Offline Multilingual Clinical Intake AI**

Gemma 4 Good Hackathon 2026 — Category: Digital Equity

---

## Overview

VoiceBridge is a fully offline, multilingual clinical intake tool for community health workers in low-connectivity settings. A nurse speaks a patient intake report in any of 40 languages. Gemma 4 E4B transcribes and translates the speech, the 26B MoE model extracts structured triage data validated against SATS 2023 and WHO ETAT guidelines, and the system produces a colour-coded printable triage form — with zero internet dependency after initial setup.

The entire stack runs on an $80 Raspberry Pi 5 or any Android tablet. The server-side path runs the full 26B MoE model via llama.cpp on an RTX 5090 for the primary demo.

---

## Key Numbers

- Prize pool: $200,000 across general, impact, and technical categories
- Submission deadline: May 18, 2026
- Judging weights: Innovation 30%, Impact Potential 30%, Technical Execution 25%, Accessibility 15%
- Target latency: < 8 seconds on Raspberry Pi 5 for a 10-second audio clip

---

## Repository Structure

```
voicebridge/
├── api/          # FastAPI backend
├── models/       # Model loading and inference wrappers
├── pipeline/     # Audio → transcript → triage logic
├── frontend/     # HTML/JS UI + service worker
├── scripts/      # Benchmarking, fine-tune prep, quantisation
├── data/         # Triage schema, language lists, SATS mappings
├── docs/         # Writeup, diagrams, benchmark results
├── tests/        # Unit and integration tests
└── docker/       # Dockerfile for reproducible demo
```

---

## Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11 |
| API | FastAPI + uvicorn |
| Edge model | Gemma 4 E4B (via transformers) |
| Server model | Gemma 4 26B MoE (via llama.cpp) |
| Fine-tuning | Unsloth LoRA |
| PDF output | reportlab |
| Database | SQLite via SQLAlchemy |
| Audio | librosa + soundfile |
| Language ID | facebook/mms-lid-256 |

---

## Setup

### Prerequisites

- Conda (Miniconda or Anaconda)
- CUDA 12.8 for GPU inference (RTX series)
- ~40 GB disk space for models

### Environment

```bash
conda create -n voicebridge python=3.11 -y
conda activate voicebridge

pip install fastapi uvicorn httpx pydantic sqlalchemy
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install transformers accelerate bitsandbytes unsloth
pip install librosa soundfile reportlab langdetect pytest httpx
```

### Running the API

```bash
conda activate voicebridge
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Clinical Standards

- Triage schema aligned with **SATS 2023** (South African Triage Scale)
- Paediatric triage follows **WHO ETAT** guidelines
- All synthetic test data — no real patient information anywhere in the codebase

---

## Supported Languages (40+)

Swahili, Tagalog, Hausa, Bengali, Hindi, Urdu, Amharic, Yoruba, Igbo, French, Portuguese, Spanish, English, Arabic, Indonesian, and 25+ more via facebook/mms-lid-256 (256-language coverage).

---

## Milestones

| Date | Milestone |
|------|-----------|
| Apr 13 | Environment setup complete — model running and smoke-tested |
| Apr 20 | Core pipeline working end-to-end: audio in, triage JSON out, PDF generated |
| Apr 27 | Clinical validation doc complete, NGO outreach emails sent |
| May 4  | LoRA fine-tune complete, benchmark suite run |
| May 11 | Demo video filmed and edited, technical writeup drafted |
| May 17 | Final submission submitted |

---

## License

Apache 2.0

---

*Built for the Gemma 4 Good Hackathon 2026 — Digital Equity category.*
