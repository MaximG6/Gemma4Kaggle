# VoiceBridge — Base vs Fine-tuned Model Comparison

Benchmark: 20 cases (4 per SATS level), 5 languages (sw, tl, ha, bn, en). Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload (-ngl 99).

## Overall Metrics

| Metric | Base Gemma 4 E4B | Fine-tuned VoiceBridge | Delta |
|--------|:----------------:|:----------------------:|------:|
| Exact match accuracy | 70.0% | 90.0% | +20.0% |
| Safe escalation rate | 90.0% | 100.0% | +10.0% |
| Unsafe under-triage cases | 2 | 0 | -2 |
| SATS validator agreement | 75.0% | 85.0% | +10.0% |

## Per-Level Accuracy

| SATS Level | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |
|------------|:--------:|:--------:|:---------:|:---------:|------:|
| RED    | 4/4 | 100.0% | 4/4 | 100.0% | +0.0% |
| ORANGE | 3/4 | 75.0% | 4/4 | 100.0% | +25.0% |
| YELLOW | 2/4 | 50.0% | 3/4 | 75.0% | +25.0% |
| GREEN  | 4/4 | 100.0% | 4/4 | 100.0% | +0.0% |
| BLUE   | 1/4 | 25.0% | 3/4 | 75.0% | +50.0% |

## Per-Language Accuracy

| Language | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |
|----------|:--------:|:--------:|:---------:|:---------:|------:|
| Bengali | 1/2 | 50.0% | 2/2 | 100.0% | +50.0% |
| English | 4/5 | 80.0% | 5/5 | 100.0% | +20.0% |
| Hausa | 2/4 | 50.0% | 3/4 | 75.0% | +25.0% |
| Swahili | 4/5 | 80.0% | 5/5 | 100.0% | +20.0% |
| Tagalog | 3/4 | 75.0% | 3/4 | 75.0% | +0.0% |

## Inference Latency (Fine-tuned, llama-cli + RTX 5090)

| Metric | Value |
|--------|------:|
| mean_s | 6.24s |
| median_s | 6.4s |
| p50_s | 6.43s |
| p95_s | 7.73s |
| min_s | 4.62s |
| max_s | 7.73s |

## Per-Case Results

| ID | Lang | Expected | Base | Tuned | Base Safe | Tuned Safe |
|----|------|----------|------|-------|:---------:|:----------:|
| R01 | SW | RED | RED | RED | ✓ | ✓ |
| R02 | TL | RED | RED | RED | ✓ | ✓ |
| R03 | HA | RED | RED | RED | ✓ | ✓ |
| R04 | EN | RED | RED | RED | ✓ | ✓ |
| O01 | BN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O02 | SW | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O03 | EN | ORANGE | GREEN | ORANGE | ✗ ⚠ | ✓ |
| O04 | TL | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| Y01 | HA | YELLOW | ORANGE | ORANGE | ✓ | ✓ |
| Y02 | BN | YELLOW | GREEN | YELLOW | ✗ ⚠ | ✓ |
| Y03 | EN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y04 | SW | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| G01 | TL | GREEN | GREEN | GREEN | ✓ | ✓ |
| G02 | EN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G03 | HA | GREEN | GREEN | GREEN | ✓ | ✓ |
| G04 | SW | GREEN | GREEN | GREEN | ✓ | ✓ |
| B01 | EN | BLUE | BLUE | BLUE | ✓ | ✓ |
| B02 | TL | BLUE | RED | RED | ✓ | ✓ |
| B03 | SW | BLUE | GREEN | BLUE | ✓ | ✓ |
| B04 | HA | BLUE | RED | BLUE | ✓ | ✓ |

## Clinical Interpretation

Fine-tuning Gemma 4 E4B on the VoiceBridge triage dataset produces a clinically meaningful improvement. Safe escalation rate: 90.0% to 100.0% (+10 pp), with 2 fewer unsafe under-triage cases. RED accuracy: 100.0% to 100.0%. Overall accuracy: +20.0 pp (70.0% to 90.0%). SATS validator agreement: +10.0 pp. All results from real llama-cli GGUF inference with RTX 5090 GPU offload.
