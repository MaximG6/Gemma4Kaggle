# VoiceBridge — Base vs Fine-tuned Model Comparison

Benchmark: 20 cases (4 per SATS level), 5 languages (sw, tl, ha, bn, en). Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload (-ngl 99).

## Overall Metrics

| Metric | Base Gemma 4 E4B | Fine-tuned VoiceBridge | Delta |
|--------|:----------------:|:----------------------:|------:|
| Exact match accuracy | 85.0% | 96.0% | +11.0% |
| Safe escalation rate | 89.0% | 100.0% | +11.0% |
| Unsafe under-triage cases | 11 | 0 | -11 |
| SATS validator agreement | 76.0% | 85.0% | +9.0% |

## Per-Level Accuracy

| SATS Level | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |
|------------|:--------:|:--------:|:---------:|:---------:|------:|
| RED    | 19/20 | 95.0% | 20/20 | 100.0% | +5.0% |
| ORANGE | 13/20 | 65.0% | 17/20 | 85.0% | +20.0% |
| YELLOW | 17/20 | 85.0% | 19/20 | 95.0% | +10.0% |
| GREEN  | 20/20 | 100.0% | 20/20 | 100.0% | +0.0% |
| BLUE   | 16/20 | 80.0% | 20/20 | 100.0% | +20.0% |

## Per-Language Accuracy

| Language | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |
|----------|:--------:|:--------:|:---------:|:---------:|------:|
| Bengali | 15/18 | 83.3% | 18/18 | 100.0% | +16.7% |
| English | 19/22 | 86.4% | 22/22 | 100.0% | +13.6% |
| Hausa | 14/20 | 70.0% | 19/20 | 95.0% | +25.0% |
| Swahili | 19/21 | 90.5% | 18/21 | 85.7% | -4.8% |
| Tagalog | 18/19 | 94.7% | 19/19 | 100.0% | +5.3% |

## Inference Latency (Fine-tuned, llama-cli + RTX 5090)

| Metric | Value |
|--------|------:|
| mean_s | 0.89s |
| median_s | 0.7s |
| p50_s | 0.7s |
| p95_s | 0.97s |
| min_s | -0.9s |
| max_s | 16.79s |

## Per-Case Results

| ID | Lang | Expected | Base | Tuned | Base Safe | Tuned Safe |
|----|------|----------|------|-------|:---------:|:----------:|
| R01 | SW | RED | RED | RED | ✓ | ✓ |
| R02 | TL | RED | RED | RED | ✓ | ✓ |
| R03 | HA | RED | RED | RED | ✓ | ✓ |
| R04 | EN | RED | RED | RED | ✓ | ✓ |
| R05 | BN | RED | RED | RED | ✓ | ✓ |
| R06 | HA | RED | ORANGE | RED | ✗ ⚠ | ✓ |
| R07 | TL | RED | RED | RED | ✓ | ✓ |
| R08 | EN | RED | RED | RED | ✓ | ✓ |
| R09 | SW | RED | RED | RED | ✓ | ✓ |
| R10 | BN | RED | RED | RED | ✓ | ✓ |
| R11 | TL | RED | RED | RED | ✓ | ✓ |
| R12 | HA | RED | RED | RED | ✓ | ✓ |
| R13 | EN | RED | RED | RED | ✓ | ✓ |
| R14 | SW | RED | RED | RED | ✓ | ✓ |
| R15 | BN | RED | RED | RED | ✓ | ✓ |
| R16 | TL | RED | RED | RED | ✓ | ✓ |
| R17 | HA | RED | RED | RED | ✓ | ✓ |
| R18 | EN | RED | RED | RED | ✓ | ✓ |
| R19 | SW | RED | RED | RED | ✓ | ✓ |
| R20 | BN | RED | RED | RED | ✓ | ✓ |
| O01 | BN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O02 | SW | ORANGE | YELLOW | RED | ✗ ⚠ | ✓ |
| O03 | EN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O04 | TL | ORANGE | YELLOW | ORANGE | ✗ ⚠ | ✓ |
| O05 | HA | ORANGE | YELLOW | ORANGE | ✗ ⚠ | ✓ |
| O06 | SW | ORANGE | ORANGE | RED | ✓ | ✓ |
| O07 | EN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O08 | TL | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O09 | BN | ORANGE | YELLOW | ORANGE | ✗ ⚠ | ✓ |
| O10 | HA | ORANGE | YELLOW | ORANGE | ✗ ⚠ | ✓ |
| O11 | SW | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O12 | EN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O13 | TL | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O14 | BN | ORANGE | YELLOW | ORANGE | ✗ ⚠ | ✓ |
| O15 | HA | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O16 | SW | ORANGE | ORANGE | RED | ✓ | ✓ |
| O17 | EN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O18 | TL | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O19 | BN | ORANGE | YELLOW | ORANGE | ✗ ⚠ | ✓ |
| O20 | HA | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| Y01 | HA | YELLOW | YELLOW | ORANGE | ✓ | ✓ |
| Y02 | BN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y03 | EN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y04 | SW | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y05 | EN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y06 | SW | YELLOW | GREEN | YELLOW | ✗ ⚠ | ✓ |
| Y07 | HA | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y08 | TL | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y09 | BN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y10 | EN | YELLOW | GREEN | YELLOW | ✗ ⚠ | ✓ |
| Y11 | SW | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y12 | HA | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y13 | TL | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y14 | BN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y15 | EN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y16 | SW | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y17 | HA | YELLOW | GREEN | YELLOW | ✗ ⚠ | ✓ |
| Y18 | TL | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y19 | BN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y20 | EN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| G01 | TL | GREEN | GREEN | GREEN | ✓ | ✓ |
| G02 | EN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G03 | HA | GREEN | GREEN | GREEN | ✓ | ✓ |
| G04 | SW | GREEN | GREEN | GREEN | ✓ | ✓ |
| G05 | SW | GREEN | GREEN | GREEN | ✓ | ✓ |
| G06 | HA | GREEN | GREEN | GREEN | ✓ | ✓ |
| G07 | TL | GREEN | GREEN | GREEN | ✓ | ✓ |
| G08 | BN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G09 | EN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G10 | SW | GREEN | GREEN | GREEN | ✓ | ✓ |
| G11 | HA | GREEN | GREEN | GREEN | ✓ | ✓ |
| G12 | TL | GREEN | GREEN | GREEN | ✓ | ✓ |
| G13 | BN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G14 | EN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G15 | SW | GREEN | GREEN | GREEN | ✓ | ✓ |
| G16 | HA | GREEN | GREEN | GREEN | ✓ | ✓ |
| G17 | TL | GREEN | GREEN | GREEN | ✓ | ✓ |
| G18 | BN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G19 | EN | GREEN | GREEN | GREEN | ✓ | ✓ |
| G20 | SW | GREEN | GREEN | GREEN | ✓ | ✓ |
| B01 | EN | BLUE | BLUE | BLUE | ✓ | ✓ |
| B02 | TL | BLUE | BLUE | BLUE | ✓ | ✓ |
| B03 | SW | BLUE | BLUE | BLUE | ✓ | ✓ |
| B04 | HA | BLUE | RED | BLUE | ✓ | ✓ |
| B05 | EN | BLUE | BLUE | BLUE | ✓ | ✓ |
| B06 | SW | BLUE | BLUE | BLUE | ✓ | ✓ |
| B07 | HA | BLUE | BLUE | BLUE | ✓ | ✓ |
| B08 | TL | BLUE | BLUE | BLUE | ✓ | ✓ |
| B09 | BN | BLUE | BLUE | BLUE | ✓ | ✓ |
| B10 | EN | BLUE | RED | BLUE | ✓ | ✓ |
| B11 | SW | BLUE | BLUE | BLUE | ✓ | ✓ |
| B12 | HA | BLUE | GREEN | BLUE | ✓ | ✓ |
| B13 | TL | BLUE | BLUE | BLUE | ✓ | ✓ |
| B14 | BN | BLUE | BLUE | BLUE | ✓ | ✓ |
| B15 | EN | BLUE | RED | BLUE | ✓ | ✓ |
| B16 | SW | BLUE | BLUE | BLUE | ✓ | ✓ |
| B17 | HA | BLUE | BLUE | BLUE | ✓ | ✓ |
| B18 | TL | BLUE | BLUE | BLUE | ✓ | ✓ |
| B19 | BN | BLUE | BLUE | BLUE | ✓ | ✓ |
| B20 | EN | BLUE | BLUE | BLUE | ✓ | ✓ |

## Clinical Interpretation

Fine-tuning Gemma 4 E4B on the VoiceBridge triage dataset produces a clinically meaningful improvement. Safe escalation rate: 89.0% to 100.0% (+11 pp), with 11 fewer unsafe under-triage cases. RED accuracy: 95.0% to 100.0%. Overall accuracy: +11.0 pp (85.0% to 96.0%). SATS validator agreement: +9.0 pp. All results from real llama-cli GGUF inference with RTX 5090 GPU offload.
