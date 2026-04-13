#!/bin/bash
# VoiceBridge — Interactive Model Comparison
# Loads both GGUFs and lets you test prompts against either model
#
# Usage:
#   chmod +x scripts/compare_models.sh
#   ./scripts/compare_models.sh

# ---------------------------------------------------------------------------
# Config — update paths if your GGUFs are elsewhere
# ---------------------------------------------------------------------------

BASE_GGUF="$HOME/hf_cache/hub/models--unsloth--gemma-4-E4B-it-GGUF/snapshots/$(ls $HOME/hf_cache/hub/models--unsloth--gemma-4-E4B-it-GGUF/snapshots/ 2>/dev/null | head -1)/gemma-4-E4B-it-Q4_K_M.gguf"
FINE_GGUF="$HOME/voicebridge-finetuned-q4km.gguf"
LLAMA_CLI="$HOME/llama.cpp/build/bin/llama-cli"

THREADS=8
TEMP=0.1
REPEAT_PENALTY=1.3
MAX_TOKENS=400

SYSTEM_PROMPT="You are a clinical triage assistant trained on SATS 2023 and WHO ETAT guidelines.
The nurse's report language: English.
Extract structured triage data from the intake report.
Respond ONLY with a JSON object. No other text."

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
echo -e "${BOLD}================================================================${RESET}"
echo -e "${BOLD}  VoiceBridge — Model Comparison Tool${RESET}"
echo -e "${BOLD}================================================================${RESET}"

if [ ! -f "$LLAMA_CLI" ]; then
    echo -e "${RED}✗ llama-cli not found at $LLAMA_CLI${RESET}"
    exit 1
fi

# Try to find base GGUF if the path resolution failed
if [ ! -f "$BASE_GGUF" ]; then
    echo -e "${YELLOW}⚠  Auto-detected base GGUF path failed, searching...${RESET}"
    BASE_GGUF=$(find "$HOME/hf_cache" /mnt/c/Users/Maxim/.cache/huggingface -name "*gemma*4*E4B*Q4*K*M*.gguf" 2>/dev/null | head -1)
    if [ -z "$BASE_GGUF" ]; then
        echo -e "${RED}✗ Base model GGUF not found. Set BASE_GGUF path manually in this script.${RESET}"
        echo -e "  Searched for: *gemma*4*E4B*Q4*K*M*.gguf"
        exit 1
    fi
fi

if [ ! -f "$FINE_GGUF" ]; then
    echo -e "${RED}✗ Fine-tuned GGUF not found at $FINE_GGUF${RESET}"
    exit 1
fi

echo -e "${GREEN}✓ Model 1 (Base)     : $BASE_GGUF${RESET}"
echo -e "${GREEN}✓ Model 2 (Finetuned): $FINE_GGUF${RESET}"
echo -e "${GREEN}✓ llama-cli          : $LLAMA_CLI${RESET}"
echo ""

# ---------------------------------------------------------------------------
# Run inference
# ---------------------------------------------------------------------------
run_model() {
    local model_path="$1"
    local user_input="$2"
    local model_label="$3"

    local prompt="${SYSTEM_PROMPT}<end_of_turn>
<start_of_turn>user
${user_input}<end_of_turn>
<start_of_turn>model
{"

    echo -e "${CYAN}----------------------------------------------------------------${RESET}"
    echo -e "${BOLD}  Running: ${model_label}${RESET}"
    echo -e "${CYAN}----------------------------------------------------------------${RESET}"

    "$LLAMA_CLI" \
        -m "$model_path" \
        -p "<start_of_turn>system
${SYSTEM_PROMPT}<end_of_turn>
<start_of_turn>user
${user_input}<end_of_turn>
<start_of_turn>model
{" \
        -n "$MAX_TOKENS" \
        --threads "$THREADS" \
        --temp "$TEMP" \
        --repeat-penalty "$REPEAT_PENALTY" \
        --log-disable \
        2>/dev/null

    echo -e "\n${CYAN}----------------------------------------------------------------${RESET}"
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while true; do
    echo -e "${BOLD}Select model:${RESET}"
    echo -e "  ${YELLOW}1${RESET} — Base Gemma 4 E4B Q4_K_M"
    echo -e "  ${YELLOW}2${RESET} — Fine-tuned VoiceBridge Q4_K_M"
    echo -e "  ${YELLOW}b${RESET} — Run BOTH models on same input"
    echo -e "  ${YELLOW}q${RESET} — Quit"
    echo ""
    read -p "Choice: " model_choice

    if [ "$model_choice" = "q" ]; then
        echo -e "${GREEN}Exiting.${RESET}"
        break
    fi

    if [ "$model_choice" != "1" ] && [ "$model_choice" != "2" ] && [ "$model_choice" != "b" ]; then
        echo -e "${RED}Invalid choice. Enter 1, 2, b or q.${RESET}"
        continue
    fi

    echo ""
    echo -e "${BOLD}Enter patient intake (press Enter twice when done):${RESET}"
    user_input=""
    while IFS= read -r line; do
        [ -z "$line" ] && break
        user_input="${user_input}${line} "
    done
    user_input="${user_input% }"

    if [ -z "$user_input" ]; then
        echo -e "${RED}No input entered.${RESET}"
        continue
    fi

    echo ""

    case "$model_choice" in
        1)
            run_model "$BASE_GGUF" "$user_input" "Base Gemma 4 E4B Q4_K_M"
            ;;
        2)
            run_model "$FINE_GGUF" "$user_input" "Fine-tuned VoiceBridge Q4_K_M"
            ;;
        b)
            run_model "$BASE_GGUF"  "$user_input" "Base Gemma 4 E4B Q4_K_M"
            echo ""
            run_model "$FINE_GGUF" "$user_input" "Fine-tuned VoiceBridge Q4_K_M"
            ;;
    esac

    echo ""
done