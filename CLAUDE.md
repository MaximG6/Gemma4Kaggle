# VoiceBridge — Project Context

## What this project is
Offline multilingual clinical intake AI for the Gemma 4 Good Hackathon.
Deadline: May 18, 2026. Category: Digital Equity. Prize pool: $200,000.

## Full project plan
Read PLAN.md in this repo root before doing anything. It contains the
complete 6-phase plan with all tasks, code samples, and timestamps.
Always refer back to it when deciding what to build next.

## Current phase
Phase 4 complete — Tasks 4.1–4.4 done

## Completed phases
- Phase 1 complete
- Phase 2 complete
- Phase 3 complete — Tasks 3.1–3.4 done, 85 tests passing
- Phase 4 complete — LoRA fine-tuned, model comparison, dashboard, quantisation

## Phase 4 outputs
- Adapter: models/voicebridge-gemma4-triage-adapter/ (324 MB, r=32, 2 epochs)
- Merged model: uploaded to HuggingFace OminousDude/voicebridge-gemma4
- Adapter: uploaded to HuggingFace OminousDude/voicebridge-adapter
- GGUF Q4_K_M: /home/maxim/models/voicebridge-q4km.gguf (uploading to HF)
- Model comparison: docs/model_comparison.md + docs/model_comparison.json
- Dashboard: dashboard/index.html (zero-dependency, auto-refresh 30s)

## Training config (final)
- Base model: google/gemma-4-e4b-it
- Dataset: 500 examples, 450 train / 50 eval (90/10 split)
- LoRA: r=32, alpha=64, dropout=0.075, 7 modules
- Epochs: 2, effective batch: 8, lr: 2e-4 cosine
- Train loss: 0.181, eval loss: 1.565 (epoch 2, best saved)

## Stack
- Python 3.11, FastAPI, uvicorn
- Gemma 4 E4B (edge) + 26B MoE (server) via transformers + llama.cpp
- Unsloth for LoRA fine-tuning
- reportlab for PDF generation
- SQLite via SQLAlchemy
- Conda env: voicebridge (already created)

## Key constraints
- All inference must work fully offline after model download
- Triage schema must align with SATS 2023 and WHO ETAT guidelines
- Fine-tuned model must run on Raspberry Pi 5 8GB via llama.cpp
- No real patient data anywhere in the codebase
- Target latency under 8 seconds on Pi 5 for a 10-second audio clip

## Active task
Phase 5 — Demo video and technical writeup