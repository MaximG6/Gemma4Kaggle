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
    lora_dropout      = 0.05,
    target_modules    = ["q_proj", "k_proj", "v_proj", "o_proj"],
    # Training
    epochs            = 4,
    per_device_batch  = 4,
    grad_accumulation = 2,      # effective batch size = 4 × 2 = 8
    learning_rate     = 2e-4,
    lr_scheduler      = "cosine",
    warmup_ratio      = 0.05,
    max_seq_length    = 4096,
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

    def on_log(self, args, state, control, logs=None, **kwargs):
        """Called by HF Trainer on every logging event."""
        if logs is None:
            return
        step = state.global_step
        if step % self.log_steps != 0:
            return
        entry = {
            "step":      step,
            "epoch":     round(state.epoch, 4) if state.epoch else None,
            "loss":      logs.get("loss"),
            "grad_norm": logs.get("grad_norm"),
            "lr":        logs.get("learning_rate"),
            "wall_time": time.time(),
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main fine-tune routine
# ---------------------------------------------------------------------------

def run_finetune(cfg: dict) -> None:
    # ── Imports (deferred so CLI --help works without GPU) ──────────────────
    import torch
    from datasets import Dataset
    from transformers import TrainingArguments, TrainerCallback

    try:
        from unsloth import FastLanguageModel
    except ImportError:
        print(
            "[ERROR] unsloth is not installed.\n"
            "        pip install unsloth\n"
            "        or: pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from trl import SFTTrainer, SFTConfig
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

    print(f"Loading dataset from {dataset_path} …")
    raw_records = load_jsonl(dataset_path)
    if cfg.get("dry_run"):
        raw_records = raw_records[:16]
        print(f"  [dry-run] truncated to {len(raw_records)} records")
    else:
        print(f"  {len(raw_records)} records loaded")

    formatted = [{"text": format_prompt(r)} for r in raw_records]
    dataset   = Dataset.from_list(formatted)

    # ── Load base model via Unsloth ──────────────────────────────────────────
    print(f"\nLoading {cfg['model_id']} via Unsloth …")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name     = cfg["model_id"],
        max_seq_length = cfg["max_seq_length"],
        load_in_4bit   = cfg["load_in_4bit"],
        dtype          = torch.bfloat16,
        # sm_120 (RTX 5090 / Blackwell) — Unsloth auto-detects, but we
        # explicitly allow the architecture so it doesn't fall back to eager.
        device_map     = "auto",
    )

    # ── Attach LoRA adapter ──────────────────────────────────────────────────
    print("\nAttaching LoRA adapter …")
    model = FastLanguageModel.get_peft_model(
        model,
        r                  = cfg["lora_rank"],
        lora_alpha         = cfg["lora_alpha"],
        lora_dropout       = cfg["lora_dropout"],
        target_modules     = cfg["target_modules"],
        bias               = "none",
        use_gradient_checkpointing = "unsloth",   # Unsloth optimised checkpointing
        random_state       = 42,
    )

    total_params     = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Trainable params : {trainable_params:,}  "
          f"({100 * trainable_params / total_params:.2f}% of {total_params:,})")

    # ── Prepare output directories ────────────────────────────────────────────
    for p in [cfg["adapter_output"], cfg["merged_output"],
              str(Path(cfg["log_path"]).parent)]:
        Path(p).mkdir(parents=True, exist_ok=True)

    # ── Training arguments ────────────────────────────────────────────────────
    max_steps = -1
    if cfg.get("dry_run"):
        max_steps = 10
        print("  [dry-run] max_steps = 10")

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
        optim                       = "adamw_8bit",
        weight_decay                = 0.01,
        logging_steps               = cfg["log_steps"],
        save_strategy               = "epoch",
        save_total_limit            = 2,
        report_to                   = "none",      # no wandb/tensorboard required
        seed                        = 42,
        max_seq_length              = cfg["max_seq_length"],
        dataset_text_field          = "text",
        packing                     = False,        # keep samples independent
    )

    # ── Loss logger callback ─────────────────────────────────────────────────
    loss_logger = JsonlLossLogger(cfg["log_path"], cfg["log_steps"])

    # Wrap as a HF TrainerCallback
    class _LossCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            loss_logger.on_log(args, state, control, logs=logs, **kwargs)

    # ── SFTTrainer ────────────────────────────────────────────────────────────
    print("\nInitialising SFTTrainer …")
    trainer = SFTTrainer(
        model          = model,
        tokenizer      = tokenizer,
        train_dataset  = dataset,
        args           = training_args,
        callbacks      = [_LossCallback()],
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    print(f"\nStarting training  (epochs={cfg['epochs']}, "
          f"effective_batch={cfg['per_device_batch'] * cfg['grad_accumulation']}, "
          f"lr={cfg['learning_rate']}) …\n")
    t0 = time.time()
    trainer.train()
    elapsed = time.time() - t0
    print(f"\nTraining complete in {elapsed / 60:.1f} min")

    # ── Save LoRA adapter ─────────────────────────────────────────────────────
    print(f"\nSaving LoRA adapter → {cfg['adapter_output']}")
    model.save_pretrained(cfg["adapter_output"])
    tokenizer.save_pretrained(cfg["adapter_output"])

    # ── Save merged (adapter + base weights fused) ─────────────────────────
    if not cfg.get("dry_run"):
        print(f"Saving merged model → {cfg['merged_output']}")
        print("  (this requires loading base weights in fp16; may take several minutes)")
        merged_model = model.merge_and_unload()
        merged_model.save_pretrained(
            cfg["merged_output"],
            safe_serialization=True,
            max_shard_size="4GB",
        )
        tokenizer.save_pretrained(cfg["merged_output"])
        print("  Merged model saved.")
    else:
        print("  [dry-run] Skipping merged model save.")

    print(f"\nDone. Loss log → {cfg['log_path']}")


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
    )


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
    print("=" * 64)

    run_finetune(cfg)
