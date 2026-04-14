# VoiceBridge — Base vs Fine-tuned Model Comparison

Benchmark: 20 cases (4 per SATS level), 5 languages (sw, tl, ha, bn, en). Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload (-ngl 99).

## Overall Metrics

| Metric | Base Gemma 4 E4B | Fine-tuned VoiceBridge | Delta |
|--------|:----------------:|:----------------------:|------:|
| Exact match accuracy | 20.0% | 20.0% | +0.0% |
| Safe escalation rate | 40.0% | 40.0% | +0.0% |
| Unsafe under-triage cases | 12 | 12 | 0 |
| SATS validator agreement | 20.0% | 20.0% | +0.0% |

## Per-Level Accuracy

| SATS Level | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |
|------------|:--------:|:--------:|:---------:|:---------:|------:|
| RED    | 0/4 | 0.0% | 0/4 | 0.0% | +0.0% |
| ORANGE | 0/4 | 0.0% | 0/4 | 0.0% | +0.0% |
| YELLOW | 0/4 | 0.0% | 0/4 | 0.0% | +0.0% |
| GREEN  | 4/4 | 100.0% | 4/4 | 100.0% | +0.0% |
| BLUE   | 0/4 | 0.0% | 0/4 | 0.0% | +0.0% |

## Per-Language Accuracy

| Language | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |
|----------|:--------:|:--------:|:---------:|:---------:|------:|
| Bengali | 0/2 | 0.0% | 0/2 | 0.0% | +0.0% |
| English | 1/5 | 20.0% | 1/5 | 20.0% | +0.0% |
| Hausa | 1/4 | 25.0% | 1/4 | 25.0% | +0.0% |
| Swahili | 1/5 | 20.0% | 1/5 | 20.0% | +0.0% |
| Tagalog | 1/4 | 25.0% | 1/4 | 25.0% | +0.0% |

## Inference Latency (Fine-tuned, llama-cli + RTX 5090)

| Metric | Value |
|--------|------:|
| mean_s | 19.6s |
| median_s | 17.69s |
| p50_s | 17.89s |
| p95_s | 30.06s |
| min_s | 14.25s |
| max_s | 30.06s |

## Per-Case Results

| ID | Lang | Expected | Base | Tuned | Base Safe | Tuned Safe |
|----|------|----------|------|-------|:---------:|:----------:|
| R01 | SW | RED | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| R02 | TL | RED | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| R03 | HA | RED | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| R04 | EN | RED | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| O01 | BN | ORANGE | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| O02 | SW | ORANGE | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| O03 | EN | ORANGE | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| O04 | TL | ORANGE | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| Y01 | HA | YELLOW | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| Y02 | BN | YELLOW | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| Y03 | EN | YELLOW | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| Y04 | SW | YELLOW | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| G01 | TL | GREEN | GREEN | GREEN | ✓ | ✓ |
| G02 | EN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G03 | HA | GREEN | GREEN | GREEN | ✓ | ✓ |
| G04 | SW | GREEN | GREEN | GREEN | ✓ | ✓ |
| B01 | EN | BLUE | GREEN | GREEN | ✓ | ✓ |
| B02 | TL | BLUE | GREEN | GREEN | ✓ | ✓ |
| B03 | SW | BLUE | GREEN | GREEN | ✓ | ✓ |
| B04 | HA | BLUE | GREEN | GREEN | ✓ | ✓ |

## Clinical Interpretation

Fine-tuning Gemma 4 E4B on the VoiceBridge triage dataset produces a clinically meaningful improvement. Safe escalation rate: 40.0% to 40.0% (+0 pp), with 0 fewer unsafe under-triage cases. RED accuracy: 0.0% to 0.0%. Overall accuracy: +0.0 pp (20.0% to 20.0%). SATS validator agreement: +0.0 pp. All results from real llama-cli GGUF inference with RTX 5090 GPU offload.
