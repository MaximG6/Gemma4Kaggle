# VOICEBRIDGE
## Offline Multilingual Clinical Intake AI
### Gemma 4 Good Hackathon 2026 — Full Project Plan

**Category:** Digital Equity | **Deadline:** May 18, 2026 | **Prize Pool:** $200,000

---

## Overview

VoiceBridge is a fully offline, multilingual clinical intake tool for community health workers in low-connectivity settings. A nurse speaks a patient intake report in any of 40+ languages. Gemma 4 E4B transcribes and translates the speech, extracts structured triage data validated against SATS 2023 and WHO ETAT guidelines, and produces a colour-coded printable triage form — with zero internet dependency after initial setup.

The entire stack runs on an $80 Raspberry Pi 5 or any Android tablet. The server-side demo path runs the full fine-tuned model via llama.cpp on an RTX 5090.

---

## Key Numbers

- Prize pool: $200,000 across general, impact, and technical categories
- Submission deadline: May 18, 2026
- Judging weights: Innovation 30%, Impact Potential 30%, Technical Execution 25%, Accessibility 15%
- Estimated win probability: 20-40% for a prize, 5-10% for top 3
- Prior precedent: Gemma 3n Impact Challenge received 600+ submissions; 8 winners

---

## Why Digital Equity Category

- Less saturated than Health & Sciences and Future of Education
- Perfectly aligned with Gemma 4's offline-first architecture
- Prior Gemma 3n winners were overwhelmingly accessibility and access-gap projects
- RTX 5090 + Pi 5 hardware demo is more polished than most competitors

---

## Milestone Status

| Date | Milestone | Status |
|---|---|---|
| Apr 13 | Environment setup, models running | ✓ DONE |
| Apr 20 | Core pipeline end-to-end: audio in, triage JSON out, PDF generated | ✓ DONE |
| Apr 27 | Clinical validation doc, NGO outreach emails sent | ✓ DONE |
| May 4 | LoRA fine-tune complete, benchmark suite run, GGUF uploaded | ✓ DONE |
| May 11 | Demo video filmed and edited, technical writeup drafted | IN PROGRESS |
| May 17 | Final submission — one day buffer before deadline | PENDING |

---

## Hardware and Environment

**Desktop:** MAXIM-12700K, RTX 5090 32GB VRAM, CUDA 12.8, sm_120 (Blackwell), Windows 11 + WSL2 Ubuntu-24.04

**Laptop:** Acer Aspire 14 AI, Windows + WSL2 Ubuntu-24.04 + dual-boot stealth LUKS Ubuntu

**Conda env:** `voicebridge` (Python 3.11)

**Repo path:** `/mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge`

**WSL config:** `memory=24GB, swap=8GB` in `C:\Users\Maxim\.wslconfig`

**HF cache:** `~/hf_cache` on `/dev/sde` Linux partition (831GB free) — set via `HF_HOME=~/hf_cache` in conda activate.d

**HF token:** stored in `~/miniconda3/envs/voicebridge/etc/conda/activate.d/env_vars.sh`

**llama.cpp:** built at `~/llama.cpp` (both `llama-quantize` and `llama-cli` confirmed working)

---

## HuggingFace Repos

| Repo | Contents | Status |
|---|---|---|
| `OminousDude/voicebridge-adapter` | Fine-tuned LoRA adapter (rank 32, ~1GB) | ✓ Uploaded |
| `OminousDude/voicebridge-gemma4` | Merged Q4_K_M GGUF (5.34GB) | ✓ Uploaded |

**Note:** Always set `HF_HUB_DISABLE_XET=1` before uploading — XET protocol causes I/O errors in WSL.

---

## Phase 1 — Foundation and Environment Setup ✓ COMPLETE

**Duration:** Apr 9-13

### Completed
- GitHub repo scaffold with full folder structure
- `voicebridge` conda env (Python 3.11) on both desktop and laptop
- PyTorch nightly cu128 (sm_120 Blackwell architecture support)
- WSL2 Ubuntu-24.04 configured as primary dev environment
- llama.cpp built from source with CUDA support
- Gemma 4 E4B downloaded and smoke-tested
- Audio capture FastAPI endpoints (file upload + WebSocket streaming)
- Language detection module (40+ languages via facebook/mms-lid-256)

### Key Decision
Used llama.cpp GGUF inference path instead of transformers for production inference — avoids the Gemma4ClippableLinear / PEFT / accelerate compatibility issues that plague the Python inference path.

---

## Phase 2 — Core Inference Pipeline ✓ COMPLETE

**Duration:** Apr 14-20

### Completed
- `GemmaTranscriber` class — audio to transcript via Gemma 4 E4B
- `TriageClassifier` — transcript to SATS-aligned triage JSON
- PDF generator — colour-coded printable triage form via ReportLab
- FastAPI backend with `/intake`, `/intake/pdf`, `/health` endpoints
- Offline mode — full pipeline with zero network dependency
- Supervisor dashboard (`dashboard/index.html`)

### Triage JSON Schema

```json
{
  "triage_level": "red",
  "primary_complaint": "...",
  "reported_symptoms": [...],
  "vital_signs_reported": {...},
  "duration_of_symptoms": "...",
  "relevant_history": "...",
  "red_flag_indicators": [...],
  "recommended_action": "...",
  "referral_needed": true,
  "confidence_score": 0.94,
  "source_language": "am",
  "raw_transcript": "..."
}
```

---

## Phase 3 — Clinical Validation and Dataset ✓ COMPLETE

**Duration:** Apr 21-27

### Completed
- `docs/clinical_validation.md` — SATS 2023 + WHO ETAT alignment document
- `data/clinical_validation.py` — rule-based SATS validator (safety net against LLM hallucination)
- `scripts/benchmark.py` — 20-case benchmark suite
- NGO outreach — 10 emails sent
- `data/finetune_train.jsonl` — 500 training examples, 8 languages

### Benchmark Results (mock classifier, Phase 3)
- Exact match: 75% (15/20)
- Safe escalation rate: 100% (zero unsafe under-triage)
- SATS validator agreement: 95%
- p95 latency: 6.47s (target <8s ✓)
- All 5 misclassifications were over-triage (clinically safe)

### Dataset Format
Each example contains `instruction` (system prompt with language), `input` (patient intake), `output` (full triage JSON). 500 examples across 8 languages: English, Swahili, Amharic, Hindi, French, Tagalog, Hausa, Bengali.

---

## Phase 4 — Fine-tuning ✓ COMPLETE

**Duration:** Apr 28-May 4 (actual: Apr 13)

### Fine-tune Configuration

| Parameter | Value | Notes |
|---|---|---|
| Base model | google/gemma-4-e4b-it | 6B params |
| Method | QLoRA via Unsloth | 4-bit quantised base |
| LoRA rank | 32 | Higher than default for structured output |
| LoRA alpha | 64 | 2x rank standard setting |
| LoRA dropout | 0.05 | |
| Target modules | q, k, v, o, gate, up, down projections | All 7 projection types |
| Epochs | 2 | |
| Batch size | 2 per device | Effective batch 8 with grad accum 4 |
| Learning rate | 2e-4 | Standard QLoRA |
| LR scheduler | cosine | |
| Optimizer | adamw_8bit | |
| Max seq length | 2048 | |
| Dataset size | 499 examples | |
| Trainable params | 84,803,584 | 1.40% of 6B |
| Training time | 5m 7s | RTX 5090 |

### Training Results

| Step | Loss | Status |
|---|---|---|
| 10 | 7.926 | Expected — in warmup |
| 20 | 2.348 | Rapid learning |
| 30 | 1.211 | Converging well |
| 40 | 0.867 | |
| 50 | 0.660 | |
| Epoch 1 eval | 1.595 | Healthy generalisation |
| 60 | 0.482 | |
| 70 | 0.367 | |
| 80 | 0.285 | |
| 90 | 0.210 | |
| 100 | 0.234 | |
| 110 | **0.176** | **Best loss** |
| Epoch 2 eval | **1.551** | Improving, no overfitting |
| Final train loss | 1.3005 | Average across all steps |

### Key Fixes Applied During Training

**Root cause of first failed run:** `dataset_text_field = None` was set incorrectly — the dataset was raw text with `instruction`/`input`/`output` fields, not pre-tokenised. This caused catastrophic loss of 7.93 that never dropped. SFTTrainer received malformed inputs.

**Fix applied:** `dataset_text_field = "text"` with `format_prompt()` building proper Gemma chat template text before passing to trainer.

**Audio tower issue:** Unsloth applied LoRA to audio tower attention layers (3978 total LoRA layers including audio tower) in addition to language model layers. For a text-only use case this is suboptimal but did not prevent the model from learning. For a future retraining run, exclude audio tower by explicitly specifying language model layer paths in target modules.

### Merge and Quantise Pipeline

Script: `scripts/merge_quantise_upload.py`

Flags:
- `--gpu` — use RTX 5090 for merge (recommended, 3-5x faster)
- `--yes` — fully unattended, skip all prompts
- `--skip-verify` — skip weight comparison step (saves ~8GB RAM peak)

**Key issue:** `Gemma4ClippableLinear` wrapper in Gemma 4 architecture causes PEFT `ValueError`. Fixed by unwrapping before adapter application:

```python
for name, module in list(model.named_modules()):
    if hasattr(module, "linear") and isinstance(module.linear, nn.Linear):
        parts = name.split(".")
        parent = model
        for part in parts[:-1]:
            parent = getattr(parent, part)
        setattr(parent, parts[-1], module.linear)
```

**GGUF output:** `~/voicebridge-finetuned-q4km.gguf` (5.34GB Q4_K_M)

**fp16 intermediate:** `~/voicebridge-finetuned-f16.gguf` (15GB, keep for requantisation)

### Inference Test Results (llama-cli on GGUF)

The fine-tuned model correctly outputs the target schema field names (`triage_level`, `primary_complaint`, `red_flag_indicators`, `recommended_action`, `confidence_score`) for a cardiac arrest prompt. The base model outputs generic fields (`reason`, `findings`, `status`).

The model produces a thinking block before the JSON output. This is intentional and kept as a feature — Gemma 4's thinking capability is a core differentiator from Gemma 3 and demonstrates clinical reasoning transparency. The pipeline parses the thinking block out before returning JSON to callers:

```python
def parse_triage_output(raw: str) -> dict:
    if "[End thinking]" in raw:
        raw = raw.split("[End thinking]")[-1].strip()
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    return json.loads(raw[start:end])
```

**Triage level format:** Model outputs `"1 - IMMEDIATE/CRITICAL"` instead of `"red"`. Fix by updating the system prompt to include: `triage_level must be one of: red, orange, yellow, green, blue.`

### Disk Management Notes

HuggingFace cache was moved from C drive to `~/hf_cache` on Linux partition (`/dev/sde`, 797GB free). C drive had 246GB of model cache at 100% capacity. Models kept on C drive: `mradermacher`, `models--jhu-clsp--mmBERT-base` (used by toxic-comments project, needed for LM Studio).

Always upload with `HF_HUB_DISABLE_XET=1` set as env var before importing huggingface_hub — XET protocol causes WSL I/O errors.

### Tools Created

- `scripts/merge_quantise_upload.py` — full merge, quantise, verify, upload pipeline
- `scripts/compare_models.sh` — interactive base vs fine-tuned comparison tool

---

## Phase 5 — Demo and Writeup (IN PROGRESS)

**Duration:** May 5-11

### Remaining Tasks

**5.1 Demo video (MOST IMPORTANT)**

Script:
1. Open on dark clinic, nurse speaks Swahili (or Amharic) into phone — airplane mode visible
2. VoiceBridge processes locally — show the thinking block briefly, then clean JSON
3. PDF prints on screen — colour-coded triage card
4. Cut to Raspberry Pi 5 hardware shot — model running on $80 device
5. Title card: "Works offline. Works anywhere. $92 total hardware cost."

Requirements:
- Under 90 seconds
- Airplane mode explicitly shown
- Non-English language spoken
- Raspberry Pi 5 hardware on camera
- No simulations — real inference running

**5.2 Kaggle writeup (11-cell notebook structure)**

| Cell | Content |
|---|---|
| 1 | Title, tagline, one-sentence description |
| 2 | Problem statement — 3.6B without healthcare access |
| 3 | Architecture diagram + system overview |
| 4 | Clinical validation — SATS and WHO ETAT alignment table |
| 5 | Fine-tune setup — model choice, dataset, training config |
| 6 | Training loss curve (matplotlib) |
| 7 | Benchmark results — accuracy, latency, safe escalation rate |
| 8 | Base model vs fine-tuned comparison (use compare_models.sh output) |
| 9 | Raspberry Pi 5 deployment — cost breakdown, latency on Pi |
| 10 | Responsible AI — limitations, safety net, clinical disclaimer |
| 11 | Conclusion + links to GitHub, HuggingFace, demo video |

**5.3 Real benchmark numbers**

Re-run `scripts/benchmark.py` with the actual GGUF model replacing the mock classifier. Update all numbers in the writeup. Target metrics to report:
- Exact match across 5 triage levels
- Safe escalation rate (must remain 100%)
- SATS validator agreement
- p50 and p95 latency (not just mean)
- Confusion matrix across triage levels
- Calibration plot of confidence_score vs correctness

**5.4 System prompt fix**

Update the production system prompt to enforce:
- `triage_level` is one of: `red`, `orange`, `yellow`, `green`, `blue`
- No extra explanation after the JSON closing brace
- Parse thinking block before returning to API callers

---

## Phase 6 — Submission Polish and Final Checks

**Duration:** May 12-17

### 6.1 Kaggle notebook — clean run
- Runs top-to-bottom with zero errors
- All output cells populated
- Requirements.txt with pinned versions committed
- All latency numbers match actual benchmark output

### 6.2 README polish
Required sections:
- Project tagline + demo GIF + Apache 2.0 badge + Hackathon badge
- One-sentence description
- Quick start: docker pull + docker run one-liner
- Hardware requirements table: Pi 5 vs server path with cost and latency
- Language support table: 40 languages with ISO code and region
- Architecture diagram
- Clinical validation note with SATS 2023 and WHO ETAT citations
- Disclaimer: not a medical device, clinical decision-support tool only

### 6.3 Docker image
```dockerfile
FROM nvidia/cuda:12.8.0-runtime-ubuntu24.04
RUN apt-get update && apt-get install -y python3.11 pip ffmpeg libsndfile1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

One-liner for judges:
```bash
docker run --gpus all -p 8000:8000 -v ./models:/models maxdev/voicebridge:latest
```

### 6.4 Final submission checklist

**Technical:**
- [ ] Kaggle notebook runs top-to-bottom with no errors
- [ ] All output cells populated
- [ ] requirements.txt with exact pinned versions committed
- [ ] pytest tests/ -v passes with zero failures
- [ ] benchmark_results.json committed to repo
- [ ] LoRA adapter on HuggingFace (`OminousDude/voicebridge-adapter`)
- [ ] GGUF on HuggingFace (`OminousDude/voicebridge-gemma4`)
- [ ] Docker image tagged and pushed to Docker Hub
- [ ] All latency numbers in writeup match actual benchmark output

**Demo and video:**
- [ ] Demo video is public (YouTube unlisted or direct upload)
- [ ] Under 90 seconds
- [ ] Airplane mode shown explicitly
- [ ] Non-English language spoken
- [ ] Raspberry Pi 5 hardware on camera

**Documentation:**
- [ ] GitHub repo is public with full commit history
- [ ] README has one-command Docker deployment
- [ ] SATS citation: Gottschalk SB et al. (2023)
- [ ] WHO ETAT citation: WHO (2016)
- [ ] Clinical disclaimer in both UI and writeup
- [ ] No real patient data in test fixtures
- [ ] NGO contact email quoted if reply received

**Category and submission:**
- [ ] Submission category: Digital Equity (NOT Health and Sciences)
- [ ] Kaggle writeup posted as public notebook
- [ ] GitHub repo link in submission
- [ ] Demo video link in submission
- [ ] Technical writeup 2,500-3,500 words

---

## Score-Boosting Extras

**Clinical narrative (judge impact: very high)**
- Lead with specific numbers: 3.6 billion lack essential healthcare, 773 million adults illiterate, 70% of CHWs have no internet
- Name specific disease burden: pneumonia kills 800,000 children under 5 annually in LMIC settings
- Quote NGO reply verbatim if received
- Personal motivation paragraph

**Technical depth signals (judge impact: high)**
- Loss curve from fine-tuning (matplotlib) — signals rigour
- Confusion matrix across 5 triage levels
- p50 and p95 latency — signals production engineering thinking
- Calibration plot of confidence_score vs actual correctness — unique and impressive
- Show the thinking block as a deliberate transparency feature — Gemma 4 specific capability not present in Gemma 3

**Accessibility and deployment proof (judge impact: high)**
- Film model actually running on Raspberry Pi 5 — not a simulation
- Docker image size and one docker run command in README
- Cost breakdown: $80 Pi + $12 SD card + free model weights = $92 total
- 40 languages listed explicitly with ISO codes

**Responsible AI (judge impact: medium)**
- Limitations section: no live clinical validation, no regulatory approval
- Rule-based SATS validator as safety net against LLM hallucination
- "Supports health workers, does not replace them"
- Data privacy: all inference local, no audio leaves device

---

## Known Issues and Technical Notes

### Python Inference (NOT for production)
Direct Python inference using Unsloth + PEFT on the adapter produces garbage output with repetition loops. Root cause: Unsloth patches the Gemma 4 architecture during training but the patched model behaves differently during autoregressive generation. **Use llama-cli with the GGUF for all inference.** Python inference is unreliable for this model.

### Gemma4ClippableLinear
All PEFT operations on Gemma 4 require unwrapping `Gemma4ClippableLinear` wrappers before applying the adapter. This is handled in `merge_quantise_upload.py`. If you see `ValueError: Target module Gemma4ClippableLinear is not supported`, add the unwrap block.

### WSL Disk Management
- Main WSL instance: `wsl -d Ubuntu-24.04`
- Linux partition: `/dev/sde`, 1007GB total, ~797GB free
- C drive: 953GB, keep above 40GB free to avoid I/O errors
- Always save model files to `~/` (Linux disk) not `/mnt/c/` during merge operations
- HF cache: `~/hf_cache` — set via `HF_HOME` env var

### XET Upload Protocol
HuggingFace's XET protocol causes `RuntimeError: Data processing error` in WSL. Always set `os.environ["HF_HUB_DISABLE_XET"] = "1"` before importing `huggingface_hub` in any upload script.

### WSL Memory Limit
Default WSL2 memory cap is 50% of system RAM. Set `memory=24GB` in `C:\Users\Maxim\.wslconfig` to prevent llama-quantize from being terminated OOM during quantisation.

### Fine-tuning Retraining (if time permits before May 18)
A second fine-tune run would improve:
- Consistent `red/orange/yellow/green/blue` triage level format
- Reduced thinking block frequency
- Audio tower excluded from target modules (reduces adapter size, prevents degradation)
- 1000+ examples instead of 500

Only do this if Phase 5 and 6 are complete with 3+ days to spare. A submitted project beats a perfect unsubmitted one.

---

## Time Budget Summary

| Phase | Duration | Key Output | Status |
|---|---|---|---|
| Phase 1 — Foundation | Apr 9-13 (4d) | Repo, env, models, audio capture | ✓ DONE |
| Phase 2 — Core pipeline | Apr 14-20 (7d) | Audio to triage JSON to PDF | ✓ DONE |
| Phase 3 — Validation | Apr 21-27 (7d) | SATS mapping, NGO outreach, benchmark, dataset | ✓ DONE |
| Phase 4 — Fine-tuning | Apr 28-May 4 (7d) | LoRA trained, GGUF quantised and uploaded | ✓ DONE |
| Phase 5 — Demo + writeup | May 5-11 (7d) | Video filmed, notebook complete, benchmarks | IN PROGRESS |
| Phase 6 — Polish | May 12-17 (6d) | Docker pushed, README polished, submitted | PENDING |

**Today's date:** April 13, 2026
**Days remaining:** 35 days until deadline

**Phases 1-4 are complete as of April 13 — 5 weeks ahead of the original Phase 4 target.**

The entire project is running significantly ahead of schedule. Use the extra time to maximise demo video quality, writeup depth, and real benchmark numbers. These have the highest return on time invested for judging.
