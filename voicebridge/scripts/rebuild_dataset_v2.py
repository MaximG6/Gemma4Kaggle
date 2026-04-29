"""
Rebuild finetune dataset with current system prompt.
Reads V1 dataset, replaces instruction field with current triage_system.txt,
substitutes language name, keeps input/output unchanged.
Outputs finetune_train_v2.jsonl.
"""
import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_JSONL  = _REPO_ROOT / "data" / "finetune_train.jsonl"
_NEW_JSONL  = _REPO_ROOT / "data" / "finetune_train_v2.jsonl"
_PROMPT_TPL = (_REPO_ROOT / "prompts" / "triage_system.txt").read_text(encoding="utf-8")

# Pattern to extract language from old instruction
_LANG_RE = re.compile(r"The nurse's report language:\s*(\S+?)\.")


def extract_language(instruction: str) -> str:
    m = _LANG_RE.search(instruction)
    if m:
        return m.group(1)
    return "English"  # fallback


def main():
    records = []
    with open(_SRC_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    print(f"Loaded {len(records)} records from {_SRC_JSONL.name}")

    lang_counts = {}
    rebuilt = []
    for i, rec in enumerate(records):
        lang = extract_language(rec.get("instruction", ""))
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

        new_rec = {
            "instruction": _PROMPT_TPL.format(lang_name=lang),
            "input": rec["input"],
            "output": rec["output"],
        }
        rebuilt.append(new_rec)

    with open(_NEW_JSONL, "w", encoding="utf-8") as f:
        for rec in rebuilt:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rebuilt)} records to {_NEW_JSONL.name}")
    print(f"\nLanguages: {dict(sorted(lang_counts.items()))}")

    # Show sample
    print(f"\n--- Sample record 0 (instruction first 300 chars) ---")
    print(rebuilt[0]["instruction"][:300])
    print(f"\n--- Sample record 0 (input first 100 chars) ---")
    print(rebuilt[0]["input"][:100])
    print(f"\n--- Sample record 0 (output first 100 chars) ---")
    print(rebuilt[0]["output"][:100])


if __name__ == "__main__":
    main()
