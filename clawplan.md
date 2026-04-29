# Claw Plan — VoiceBridge V2 Fine-Tune

**Created:** 2026-04-24 20:16 EDT
**Goal:** Retrain with current system prompt, exclude audio tower, preserve existing model

---

## What Changed from V1

| Aspect | V1 (current) | V2 (target) |
|--------|-------------|-------------|
| System prompt | Old prompt (no explicit triage_level format, no BLUE rule detail) | Current `triage_system.txt` with explicit format rules, KEY RULE, decision tree |
| Audio tower | LoRA applied to audio tower layers (3978 total LoRA layers) | Audio tower excluded — LM text layers only |
| Output path | `models/voicebridge-gemma4-triage-adapter/` (overwritten) | `models/voicebridge-gemma4-triage-adapter-v2/` (new) |
| Merged path | `models/voicebridge-merged/` (overwritten) | `models/voicebridge-merged-v2/` (new) |
| Loss log | `runs/finetune_log.jsonl` (overwritten) | `runs/finetune_log_v2.jsonl` (new) |
| Config | `runs/finetune_config.json` (overwritten) | `runs/finetune_config_v2.json` (new) |

---

## Step 1: Update Dataset with Current System Prompt

**File:** `data/finetune_train.jsonl` (500 examples)

**Problem:** The `instruction` field in each JSONL record contains the OLD system prompt. Need to replace it with the current `prompts/triage_system.txt` content (with `{lang_name}` substituted).

**Action:** Write `scripts/rebuild_dataset_v2.py` that:
1. Reads `prompts/triage_system.txt` as the new system prompt template
2. Reads each record from `data/finetune_train.jsonl`
3. Extracts the language from the old instruction (pattern: "Language: XXX")
4. Replaces the instruction with the new prompt template, substituting `{lang_name}`
5. Keeps `input` and `output` fields unchanged
6. Writes to `data/finetune_train_v2.jsonl`
7. Prints count of records processed, sample before/after comparison

**Verification:** Compare first 3 records before/after. Confirm language names match.

---

## Step 2: Modify Finetune Script to Exclude Audio Tower

**File:** `scripts/finetune.py` → create `scripts/finetune_v2.py`

**Changes needed:**

### 2a. Output paths
Change all default output paths to V2 equivalents:
- `adapter_output`: `models/voicebridge-gemma4-triage-adapter-v2`
- `merged_output`: `models/voicebridge-merged-v2`
- `log_path`: `runs/finetune_log_v2.jsonl`

### 2b. Dataset path
- `dataset_path`: `data/finetune_train_v2.jsonl`

### 2c. Audio tower exclusion
**Current code** (line ~175):
```python
model = FastLanguageModel.get_peft_model(
    model,
    target_modules = cfg['target_modules'],
    ...
)
```

**Problem:** Generic module names like `q_proj`, `k_proj` match BOTH language model layers AND audio tower layers. The audio tower has its own attention layers with the same projection names.

**Fix:** After loading the model but BEFORE applying PEFT, inspect all module names and filter to only include language model (text) layers. Specifically:
- Include modules under `model.model.layers[*].self_attn.*` and `model.model.layers[*].mlp.*` (the LM transformer blocks)
- Exclude modules under `model.vision_model.*` or `model.audio_tower.*` or any multimodal encoder path

**Implementation approach:**
```python
# After loading model, before get_peft_model:
# Get all module names that match target_modules
all_targets = []
for name, module in model.named_modules():
    if isinstance(module, torch.nn.Linear):
        # Check if this is a language model layer (not vision/audio)
        if 'layers' in name and not any(x in name for x in ['vision_model', 'audio_tower', 'multimodal']):
            for tm in cfg['target_modules']:
                if name.endswith('.' + tm):
                    all_targets.append(name)
                    break

print(f"Targeting {len(all_targets)} LM-only modules (audio tower excluded)")
model = FastLanguageModel.get_peft_model(model, target_modules=all_targets, ...)
```

### 2d. Config save path
- Write config to `runs/finetune_config_v2.json`

---

## Step 3: Run Fine-Tune

**Command (WSL, voicebridge conda env):**
```bash
cd /mnt/c/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge
python scripts/finetune_v2.py
```

**Expected parameters (same as V1):**
- LoRA rank: 32, alpha: 64, dropout: 0.075
- Epochs: 2, batch: 2, grad accum: 4 (effective 8)
- LR: 2e-4, cosine scheduler, warmup 5%
- Max seq length: 2048
- 4-bit quantized base, bf16
- adamw_8bit optimizer

**Expected results:**
- Training time: ~5 min on RTX 5090 (same as V1)
- Fewer trainable params than V1 (no audio tower layers)
- V1 had 84,803,584 trainable params (1.40% of 6B) — V2 should be less
- Loss log saved to `runs/finetune_log_v2.jsonl`

---

## Step 4: Verify Results

**Checks:**
1. Adapter saved to `models/voicebridge-gemma4-triage-adapter-v2/`
2. Merged model saved to `models/voicebridge-merged-v2/`
3. Loss curve looks healthy (should converge to ~0.1-0.3 by step 100)
4. Trainable param count is lower than V1 (audio tower excluded)
5. V1 adapter at `models/voicebridge-gemma4-triage-adapter/` is untouched

**No GGUF export or HF upload yet** — that's the next phase after verification.

---

## File Inventory

### New files created:
- `scripts/rebuild_dataset_v2.py` — dataset rebuild script
- `scripts/finetune_v2.py` — modified finetune script
- `data/finetune_train_v2.jsonl` — rebuilt dataset with current prompt
- `models/voicebridge-gemma4-triage-adapter-v2/` — new adapter (after training)
- `models/voicebridge-merged-v2/` — new merged model (after training)
- `runs/finetune_log_v2.jsonl` — new loss log
- `runs/finetune_config_v2.json` — new config

### Existing files preserved:
- `models/voicebridge-gemma4-triage-adapter/` — V1 adapter (untouched)
- `models/voicebridge-merged/` — V1 merged model (untouched)
- `runs/finetune_log.jsonl` — V1 loss log (untouched)
- `runs/finetune_config.json` — V1 config (untouched)
- `data/finetune_train.jsonl` — V1 dataset (untouched)

---

## Execution Order

1. Write `scripts/rebuild_dataset_v2.py`
2. Run it → produces `data/finetune_train_v2.jsonl`
3. Verify dataset (spot-check 3 records)
4. Write `scripts/finetune_v2.py` (copy from finetune.py with modifications)
5. Run finetune → produces V2 adapter + merged model
6. Verify results (param count, loss curve, file locations)
7. Report back — GGUF/upload is next phase

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Audio tower not properly excluded | Medium | Print all targeted module names before training, verify none contain "vision" or "audio" |
| Dataset language extraction fails | Low | Old prompt has "Language: XXX" pattern — verify with sample before full rebuild |
| VRAM OOM | Low | Same params as V1 which completed in 5m 7s |
| Training diverges | Low | Same hyperparams, just different prompt text |

---

## Next Phase (after V2 training complete)

1. Merge V2 adapter → fp16
2. Quantize to Q4_K_M GGUF
3. Run 100-case benchmark (compare V1 vs V2)
4. Upload to HuggingFace as new repo or new version
5. Update Kaggle notebook to use V2 model
