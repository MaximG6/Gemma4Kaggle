"""
VoiceBridge QLoRA Fine-Tune — Task 4.1
========================================
Fine-tunes Gemma 4 E4B on the VoiceBridge triage dataset using Unsloth +
SFTTrainer (trl). Saves the LoRA adapter and a fully-merged model.

Hardware target : RTX 5090, CUDA 12.8, sm_120, 32 GB VRAM
Base model      : google/gemma-4-e4b-it
Dataset         : data/finetune_train.jsonl  (500 examples, pre-built)
Adapter output  : models/voicebridge-gemma4-triage-adapter/
Merged output   : models/voicebridge-merged/
Loss log        : runs/finetune_log.jsonl

Usage (from voicebridge/ repo root, conda env voicebridge active):
    python scripts/finetune.py
    python scripts/finetune.py --epochs 2 --dry-run   # smoke-test 10 steps
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo-root path setup
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Hyper-parameters (all overridable via CLI flags)
# ---------------------------------------------------------------------------

DEFAULTS = dict(
    model_id          = "google/gemma-4-e4b-it",
    dataset_path      = str(_REPO_ROOT / "data" / "finetune_train.jsonl"),
    adapter_output    = str(_REPO_ROOT / "models" / "voicebridge-gemma4-triage-adapter"),
    merged_output     = str(_REPO_ROOT / "models" / "voicebridge-merged"),
    log_path          = str(_REPO_ROOT / "runs" / "finetune_log.jsonl"),
    # LoRA
    lora_rank         = 32,
    lora_alpha        = 64,
    lora_dropout      = 0.075,
    target_modules    = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    # Training
    epochs            = 2,
    per_device_batch  = 2,
    grad_accumulation = 4,      # effective batch size = 2 × 4 = 8
    learning_rate     = 2e-4,
    lr_scheduler      = "cosine",
    warmup_ratio      = 0.05,
    max_seq_length    = 2048,
    log_steps         = 10,
    # Quantisation
    load_in_4bit      = True,
)


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------

def load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def format_prompt(record: dict) -> str:
    """
    Convert a finetune_train.jsonl record into a single string that the
    Gemma chat template expects.

    Each record has:
        instruction : str   — system prompt
        input       : str   — nurse intake transcript
        output      : str   — target TriageOutput JSON

    We format as a 3-turn conversation (system / user / assistant) using
    Gemma's standard control tokens.
    """
    instruction = record.get("instruction", "")
    user_input  = record.get("input", "")
    output      = record.get("output", "")

    # Gemma 4 chat template control tokens
    return (
        "<start_of_turn>system\n"
        f"{instruction}"
        "<end_of_turn>\n"
        "<start_of_turn>user\n"
        f"{user_input}"
        "<end_of_turn>\n"
        "<start_of_turn>model\n"
        f"{output}"
        "<end_of_turn>"
    )


# ---------------------------------------------------------------------------
# Loss logger callback
# ---------------------------------------------------------------------------

class JsonlLossLogger:
    """
    Lightweight training callback that appends a JSON line to
    runs/finetune_log.jsonl every `log_steps` steps.
    Compatible with both Hugging Face TrainerCallback and direct calls.
    """

    def __init__(self, log_path: str, log_steps: int) -> None:
        self.log_path  = Path(log_path)
        self.log_steps = log_steps
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Truncate / create fresh log for this run
        self.log_path.write_text("")
        self.best_loss = float("inf")
        self.best_step = 0

    def on_log(self, args, state, control, logs=None, **kwargs):
        """Called by HF Trainer on every logging event."""
        if logs is None:
            return
        step = state.global_step
        if step % self.log_steps != 0:
            return
        loss = logs.get("loss")
        if loss is not None and loss < self.best_loss:
            self.best_loss = loss
            self.best_step = step
        entry = {
            "step":          step,
            "epoch":         round(state.epoch, 4) if state.epoch else None,
            "loss":          loss,
            "learning_rate": logs.get("learning_rate"),
            "timestamp":     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main fine-tune routine
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Per-print elapsed-time helper (module-level so all entry points can use it)
# ---------------------------------------------------------------------------

_t_ref = [time.time()]

def _tick(msg: str, file=None) -> None:
    """Print msg prefixed with [+Xs] elapsed since the last _tick call."""
    now    = time.time()
    delta  = now - _t_ref[0]
    _t_ref[0] = now
    prefix = f"[+{delta:6.1f}s] "
    aligned = msg.replace("\n", "\n" + " " * len(prefix))
    print(prefix + aligned, flush=True, **({"file": file} if file else {}))


def run_finetune(cfg: dict) -> None:
    # ── Imports (deferred so CLI --help works without GPU) ──────────────────
    _tick("[1/7] Importing torch + CUDA (may take 20–60s on first run) …")
    import torch
    _tick(f"      torch {torch.__version__}  "
          f"CUDA available: {torch.cuda.is_available()}  "
          f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

    _tick("[2/7] Importing HuggingFace datasets + transformers …")
    from datasets import Dataset
    from transformers import TrainerCallback, DataCollatorForLanguageModeling
    _tick("      done.")

    _tick("[3/7] Importing Unsloth (may compile CUDA kernels on first run) …")
    try:
        from unsloth import FastLanguageModel
        _tick("      unsloth imported.")
    except ImportError:
        print(
            "[ERROR] unsloth is not installed.\n"
            "        pip install unsloth\n"
            "        or: pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'",
            file=sys.stderr,
        )
        sys.exit(1)

    _tick("[4/7] Importing trl …")
    try:
        from trl import SFTTrainer, SFTConfig
        _tick("      trl imported.")
    except ImportError:
        print(
            "[ERROR] trl is not installed.\n"
            "        pip install trl",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Validate dataset ─────────────────────────────────────────────────────
    dataset_path = cfg["dataset_path"]
    if not Path(dataset_path).exists():
        print(f"[ERROR] Dataset not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)

    _tick(f"\n[5/7] Loading dataset from {dataset_path} …")
    raw_records = load_jsonl(dataset_path)
    if cfg.get("dry_run"):
        raw_records = raw_records[:16]
        _tick(f"  [dry-run] truncated to {len(raw_records)} records")
    else:
        _tick(f"  {len(raw_records)} records loaded")

    # Store messages for later — dataset is built after tokenizer loads
    # so we can apply the chat template with the real tokenizer.
    formatted = [
        {
            "messages": [
                {"role": "system",    "content": r.get("instruction", "")},
                {"role": "user",      "content": r.get("input", "")},
                {"role": "assistant", "content": r.get("output", "")},
            ]
        }
        for r in raw_records
    ]

    # ── Load base model via Unsloth ──────────────────────────────────────────
    _tick(f"\n[6/7] Loading {cfg['model_id']} via Unsloth …\n"
          f"      4-bit quant: {cfg['load_in_4bit']}  "
          f"max_seq_length: {cfg['max_seq_length']}  dtype: bfloat16\n"
          f"      (downloads ~9 GB on first run, then loads into VRAM — "
          f"may take several minutes)")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name     = cfg["model_id"],
        max_seq_length = cfg["max_seq_length"],
        load_in_4bit   = cfg["load_in_4bit"],
        dtype          = torch.bfloat16,
        # sm_120 (RTX 5090 / Blackwell) — Unsloth auto-detects, but we
        # explicitly allow the architecture so it doesn't fall back to eager.
        device_map     = "auto",
    )
    _vram_gb = (torch.cuda.memory_allocated() / 1024**3
                if torch.cuda.is_available() else 0.0)
    _tick(f"      Model loaded.  VRAM used: {_vram_gb:.1f} GB")

    # Apply chat template now that tokenizer is available, producing a plain
    # "text" dataset — avoids the collator receiving raw "messages" dicts.
    _tick(f"      Applying chat template to {len(formatted)} examples …")
    dataset = Dataset.from_dict({
        "text": [
            tokenizer.apply_chat_template(
                ex["messages"], tokenize=False, add_generation_prompt=False
            )
            for ex in formatted
        ]
    })
    _tick(f"      Dataset ready  ({len(dataset)} examples)")

    # Pre-tokenise so SFTTrainer receives input_ids/labels/attention_mask directly.
    # This bypasses SFTTrainer's internal lazy tokenisation, which in trl 0.10+
    # runs _remove_unused_columns on the raw dataset before tokenising — causing
    # the "text" column to be dropped before it is ever processed.
    _tick(f"      Pre-tokenising {len(dataset)} examples …")

    def _tokenize_batch(batch):
        enc = tokenizer(
            text=batch["text"],          # keyword arg — Gemma4 processor has images first
            truncation=True,
            max_length=cfg["max_seq_length"],
            padding=False,
        )
        enc["labels"] = [ids[:] for ids in enc["input_ids"]]
        return enc

    dataset = dataset.map(_tokenize_batch, batched=True, remove_columns=["text"])
    _tick(f"      Pre-tokenised  ({len(dataset)} examples, "
          f"columns: {dataset.column_names})")

    # ── Train / eval split (90 / 10) ─────────────────────────────────────────
    # Skip split in dry-run (too few examples to split meaningfully)
    if not cfg.get("dry_run") and len(dataset) >= 20:
        split       = dataset.train_test_split(test_size=0.1, seed=42)
        train_data  = split["train"]
        eval_data   = split["test"]
        _tick(f"      Train/eval split: {len(train_data)} train / {len(eval_data)} eval")
    else:
        train_data = dataset
        eval_data  = None
        _tick(f"      No eval split (dry-run or too few examples).")

    # ── Attach LoRA adapter ──────────────────────────────────────────────────
    _tick(f"      Attaching LoRA adapter "
          f"(r={cfg['lora_rank']}, α={cfg['lora_alpha']}, "
          f"modules={len(cfg['target_modules'])}) …")
    model = FastLanguageModel.get_peft_model(
        model,
        r                          = cfg["lora_rank"],
        lora_alpha                 = cfg["lora_alpha"],
        lora_dropout               = cfg["lora_dropout"],
        target_modules             = cfg["target_modules"],
        bias                       = "none",
        use_gradient_checkpointing = "unsloth",
        random_state               = 42,
    )

    total_params     = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    _tick(f"      Trainable params: {trainable_params:,}  "
          f"({100 * trainable_params / total_params:.2f}% of {total_params:,})")

    # ── Prepare output directories ────────────────────────────────────────────
    runs_dir = Path(cfg["log_path"]).parent
    for p in [cfg["adapter_output"], cfg["merged_output"], str(runs_dir)]:
        Path(p).mkdir(parents=True, exist_ok=True)

    # ── Write run config snapshot ─────────────────────────────────────────────
    run_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    finetune_config = {
        "model_id":              cfg["model_id"],
        "lora_rank":             cfg["lora_rank"],
        "lora_alpha":            cfg["lora_alpha"],
        "lora_dropout":          cfg["lora_dropout"],
        "target_modules":        cfg["target_modules"],
        "load_in_4bit":          cfg["load_in_4bit"],
        "epochs":                cfg["epochs"],
        "batch_size":            cfg["per_device_batch"],
        "grad_accum":            cfg["grad_accumulation"],
        "effective_batch_size":  cfg["per_device_batch"] * cfg["grad_accumulation"],
        "learning_rate":         cfg["learning_rate"],
        "lr_scheduler":          cfg["lr_scheduler"],
        "max_seq_len":           cfg["max_seq_length"],
        "optimizer":             "adamw_8bit",
        "bf16":                  True,
        "dataset_path":          cfg["dataset_path"],
        "dataset_size":          len(raw_records),
        "adapter_output_path":   cfg["adapter_output"],
        "merged_output_path":    cfg["merged_output"],
        "hardware_note":         "RTX 5090 32GB VRAM, CUDA 12.8, sm_120 (Blackwell)",
        "run_timestamp":         run_timestamp,
    }
    config_json_path = runs_dir / "finetune_config.json"
    config_json_path.write_text(json.dumps(finetune_config, indent=2))
    _tick(f"  Run config saved → {config_json_path}")

    # ── Training arguments ────────────────────────────────────────────────────
    max_steps = -1
    if cfg.get("dry_run"):
        max_steps = 10
        _tick("  [dry-run] max_steps = 10")

    training_args = SFTConfig(
        output_dir                  = cfg["adapter_output"],
        num_train_epochs            = cfg["epochs"] if max_steps == -1 else 1,
        max_steps                   = max_steps,
        per_device_train_batch_size = cfg["per_device_batch"],
        gradient_accumulation_steps = cfg["grad_accumulation"],
        learning_rate               = cfg["learning_rate"],
        lr_scheduler_type           = cfg["lr_scheduler"],
        warmup_ratio                = cfg["warmup_ratio"],
        bf16                        = True,
        fp16                        = False,
        gradient_checkpointing      = True,
        optim                       = "adamw_8bit",
        weight_decay                = 0.01,
        logging_steps               = cfg["log_steps"],
        save_strategy               = "epoch",
        save_total_limit            = 2,
        eval_strategy               = "epoch" if eval_data is not None else "no",
        load_best_model_at_end      = eval_data is not None,
        metric_for_best_model       = "eval_loss",
        greater_is_better           = False,
        report_to                   = "none",
        seed                        = 42,
        dataset_text_field          = "text",
        packing                     = False,
    )

    # ── Loss logger callback ─────────────────────────────────────────────────
    loss_logger = JsonlLossLogger(cfg["log_path"], cfg["log_steps"])

    class _LossCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            loss_logger.on_log(args, state, control, logs=logs, **kwargs)

    # ── SFTTrainer ────────────────────────────────────────────────────────────
    _tick(f"\n[7/7] Initialising SFTTrainer …\n"
          f"      Tokenising {len(dataset)} examples "
          f"(max_seq_length={cfg['max_seq_length']}) — may take 1–2 min …")

    trainer = SFTTrainer(
        model          = model,
        tokenizer      = tokenizer,
        train_dataset  = train_data,
        eval_dataset   = eval_data,
        data_collator  = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        args           = training_args,
        callbacks      = [_LossCallback()],
    )
    _tick(f"      SFTTrainer ready.  "
          f"{len(trainer.train_dataset)} training examples"
          + (f" / {len(eval_data)} eval examples." if eval_data else "."))

    # ── Train ─────────────────────────────────────────────────────────────────
    _eff_batch   = cfg["per_device_batch"] * cfg["grad_accumulation"]
    _total_steps = (len(trainer.train_dataset) // _eff_batch) * cfg["epochs"]
    _tick(f"\nStarting training …\n"
          f"  epochs={cfg['epochs']}  effective_batch={_eff_batch}  "
          f"lr={cfg['learning_rate']}  est. steps≈{_total_steps}\n"
          f"  Loss logged every {cfg['log_steps']} steps → {cfg['log_path']}\n"
          f"  (HF Trainer progress bar below)\n")
    t0 = time.time()
    train_result = trainer.train()
    elapsed = time.time() - t0
    _tick(f"\nTraining complete in {elapsed / 60:.1f} min")

    # ── Save LoRA adapter ─────────────────────────────────────────────────────
    _tick(f"\nSaving LoRA adapter → {cfg['adapter_output']}")
    model.save_pretrained(cfg["adapter_output"])
    tokenizer.save_pretrained(cfg["adapter_output"])
    _tick("  Adapter saved.")

    # ── Save merged (adapter + base weights fused) ─────────────────────────
    if not cfg.get("dry_run"):
        _tick(f"\nSaving merged model → {cfg['merged_output']}\n"
              f"  (fusing + dequantising LoRA weights to fp16 — may take several minutes)")
        model.save_pretrained_merged(
            cfg["merged_output"],
            tokenizer,
            save_method = "merged_16bit",
        )
        _tick("  Merged model saved (fp16, GGUF-ready).")
    else:
        _tick("  [dry-run] Skipping merged model save.")
        _tick("\n[dry-run] Testing inference on one example...")
        FastLanguageModel.for_inference(model)
        # Build prompt from messages (system + user only — no assistant turn)
        _msgs  = formatted[0]["messages"][:2]
        sample = tokenizer.apply_chat_template(
            _msgs, tokenize=False, add_generation_prompt=True
        )
        inputs  = tokenizer(text=sample, return_tensors="pt").to("cuda")
        outputs = model.generate(**inputs, max_new_tokens=256)
        _tick(tokenizer.decode(outputs[0], skip_special_tokens=True)[-500:])

    # ── Training summary ──────────────────────────────────────────────────────
    final_loss  = train_result.training_loss
    best_loss   = loss_logger.best_loss
    best_step   = loss_logger.best_step
    h, rem      = divmod(int(elapsed), 3600)
    m, s        = divmod(rem, 60)
    elapsed_str = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"

    _tick("\n" + "=" * 64 + "\n"
          "Training Summary\n"
          + "=" * 64 + "\n"
          f"  Final training loss      : {final_loss:.4f}\n"
          f"  Best loss achieved       : {best_loss:.4f}  (step {best_step})\n"
          f"  Total training time      : {elapsed_str}\n"
          f"  Trainable parameters     : {trainable_params:,}  "
          f"({100 * trainable_params / total_params:.2f}% of {total_params:,})\n"
          f"  Adapter saved            : {cfg['adapter_output']}"
          + (f"\n  Merged model saved       : {cfg['merged_output']}"
             if not cfg.get("dry_run") else "") + "\n"
          f"  Loss log                 : {cfg['log_path']}\n"
          + "=" * 64)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> dict:
    parser = argparse.ArgumentParser(
        description="VoiceBridge QLoRA fine-tune — Gemma 4 E4B"
    )
    parser.add_argument("--model-id",          default=DEFAULTS["model_id"])
    parser.add_argument("--dataset-path",      default=DEFAULTS["dataset_path"])
    parser.add_argument("--adapter-output",    default=DEFAULTS["adapter_output"])
    parser.add_argument("--merged-output",     default=DEFAULTS["merged_output"])
    parser.add_argument("--log-path",          default=DEFAULTS["log_path"])
    parser.add_argument("--epochs",            type=int,   default=DEFAULTS["epochs"])
    parser.add_argument("--batch-size",        type=int,   default=DEFAULTS["per_device_batch"])
    parser.add_argument("--grad-accum",        type=int,   default=DEFAULTS["grad_accumulation"])
    parser.add_argument("--lr",                type=float, default=DEFAULTS["learning_rate"])
    parser.add_argument("--lora-rank",         type=int,   default=DEFAULTS["lora_rank"])
    parser.add_argument("--lora-alpha",        type=int,   default=DEFAULTS["lora_alpha"])
    parser.add_argument("--max-seq-length",    type=int,   default=DEFAULTS["max_seq_length"])
    parser.add_argument("--log-steps",         type=int,   default=DEFAULTS["log_steps"])
    parser.add_argument("--dry-run",           action="store_true",
                        help="Run 10 steps on 16 examples to validate the setup")
    parser.add_argument("--merge-only",        action="store_true",
                        help="Skip training — load saved adapter and merge into base model")
    args = parser.parse_args()

    return dict(
        model_id          = args.model_id,
        dataset_path      = args.dataset_path,
        adapter_output    = args.adapter_output,
        merged_output     = args.merged_output,
        log_path          = args.log_path,
        lora_rank         = args.lora_rank,
        lora_alpha        = args.lora_alpha,
        lora_dropout      = DEFAULTS["lora_dropout"],
        target_modules    = DEFAULTS["target_modules"],
        epochs            = args.epochs,
        per_device_batch  = args.batch_size,
        grad_accumulation = args.grad_accum,
        learning_rate     = args.lr,
        lr_scheduler      = DEFAULTS["lr_scheduler"],
        warmup_ratio      = DEFAULTS["warmup_ratio"],
        max_seq_length    = args.max_seq_length,
        load_in_4bit      = DEFAULTS["load_in_4bit"],
        log_steps         = args.log_steps,
        dry_run           = args.dry_run,
        merge_only        = args.merge_only,
    )


# ---------------------------------------------------------------------------
# Merge-only path (--merge-only)
# ---------------------------------------------------------------------------

def run_merge_only(cfg: dict) -> None:
    """Load base model + saved LoRA adapter, fuse weights, save merged model."""
    from unsloth import FastLanguageModel

    adapter_path = cfg["adapter_output"]
    merged_path  = cfg["merged_output"]

    if not Path(adapter_path).exists():
        print(f"[ERROR] Adapter not found at {adapter_path}", flush=True)
        sys.exit(1)

    print(f"  Adapter  : {adapter_path}", flush=True)
    print(f"  Merged → : {merged_path}", flush=True)
    print("=" * 64, flush=True)

    _tick("Loading base model + adapter …")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name     = adapter_path,   # loads base + applies adapter
        max_seq_length = cfg["max_seq_length"],
        load_in_4bit   = cfg["load_in_4bit"],
    )
    _tick("  Model loaded.")

    gguf_path = str(Path(merged_path).parent / "voicebridge-q4km.gguf")
    _tick(f"\nSaving directly to GGUF Q4_K_M → {gguf_path}\n"
          f"  (bypasses fp16 intermediate — less RAM required)")
    model.save_pretrained_gguf(
        str(Path(merged_path).parent / "voicebridge"),
        tokenizer,
        quantization_method = "q4_k_m",
    )
    _tick(f"  GGUF saved → {gguf_path}")


if __name__ == "__main__":
    cfg = parse_args()

    print("=" * 64)
    print("VoiceBridge QLoRA Fine-Tune")
    print("=" * 64)
    print(f"  Model          : {cfg['model_id']}")
    print(f"  Dataset        : {cfg['dataset_path']}")
    print(f"  LoRA rank/α    : {cfg['lora_rank']} / {cfg['lora_alpha']}")
    print(f"  Target modules : {cfg['target_modules']}")
    print(f"  Epochs         : {cfg['epochs']}")
    print(f"  Effective batch: {cfg['per_device_batch'] * cfg['grad_accumulation']}")
    print(f"  Learning rate  : {cfg['learning_rate']}")
    print(f"  Scheduler      : {cfg['lr_scheduler']}  (warmup {cfg['warmup_ratio']})")
    print(f"  Max seq len    : {cfg['max_seq_length']}")
    print(f"  Adapter → {cfg['adapter_output']}")
    print(f"  Merged  → {cfg['merged_output']}")
    print(f"  Loss log→ {cfg['log_path']}")
    if cfg.get("dry_run"):
        print("  MODE           : DRY RUN (10 steps)")
    if cfg.get("merge_only"):
        print("  MODE           : MERGE ONLY (no training)")
    print("=" * 64)

    if cfg.get("merge_only"):
        run_merge_only(cfg)
    else:
        run_finetune(cfg)
