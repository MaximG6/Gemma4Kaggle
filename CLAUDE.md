# VoiceBridge — Project Context

## What this project is
Offline multilingual clinical intake AI for the Gemma 4 Good Hackathon.
Deadline: May 18, 2026. Category: Digital Equity. Prize pool: $200,000.

## Full project plan
Read PLAN.md in this repo root before doing anything. It contains the
complete 6-phase plan with all tasks, code samples, and timestamps.
Always refer back to it when deciding what to build next.

## Current phase
Phase 2 complete — all 5 tasks done, 85 tests passing

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
Phase 3 — Task 3.1 (SATS/ETAT clinical validation mapping)