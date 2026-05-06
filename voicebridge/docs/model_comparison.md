# VoiceBridge — Base vs Fine-tuned Model Comparison

Benchmark: 20 cases (4 per SATS level), 5 languages (sw, tl, ha, bn, en). Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload (-ngl 99).

## Overall Metrics

| Metric | Base Gemma 4 E4B | Fine-tuned VoiceBridge | Delta |
|--------|:----------------:|:----------------------:|------:|
| Exact match accuracy | 74.0% | 89.0% | +15.0% |
| Safe escalation rate | 89.0% | 98.0% | +9.0% |
| Unsafe under-triage cases | 11 | 2 | -9 |
| SATS validator agreement | 74.0% | 84.0% | +10.0% |

## Per-Level Accuracy

| SATS Level | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |
|------------|:--------:|:--------:|:---------:|:---------:|------:|
| RED    | 19/20 | 95.0% | 20/20 | 100.0% | +5.0% |
| ORANGE | 14/20 | 70.0% | 17/20 | 85.0% | +15.0% |
| YELLOW | 15/20 | 75.0% | 18/20 | 90.0% | +15.0% |
| GREEN  | 20/20 | 100.0% | 18/20 | 90.0% | -10.0% |
| BLUE   | 6/20 | 30.0% | 16/20 | 80.0% | +50.0% |

## Per-Language Accuracy

| Language | Base n/N | Base acc | Tuned n/N | Tuned acc | Delta |
|----------|:--------:|:--------:|:---------:|:---------:|------:|
| Bengali | 15/18 | 83.3% | 16/18 | 88.9% | +5.6% |
| English | 14/22 | 63.6% | 18/22 | 81.8% | +18.2% |
| Hausa | 15/20 | 75.0% | 20/20 | 100.0% | +25.0% |
| Swahili | 15/21 | 71.4% | 19/21 | 90.5% | +19.1% |
| Tagalog | 15/19 | 78.9% | 16/19 | 84.2% | +5.3% |

## Inference Latency (Fine-tuned, llama-cli + RTX 5090)

| Metric | Value |
|--------|------:|
| mean_s | 7.38s |
| median_s | 7.38s |
| p50_s | 7.43s |
| p95_s | 9.44s |
| min_s | 4.88s |
| max_s | 15.1s |

## Per-Case Results

| ID | Lang | Expected | Base | Tuned | Base Safe | Tuned Safe |
|----|------|----------|------|-------|:---------:|:----------:|
| R01 | SW | RED | RED | RED | ✓ | ✓ |
| R02 | TL | RED | RED | RED | ✓ | ✓ |
| R03 | HA | RED | RED | RED | ✓ | ✓ |
| R04 | EN | RED | RED | RED | ✓ | ✓ |
| R05 | BN | RED | RED | RED | ✓ | ✓ |
| R06 | HA | RED | RED | RED | ✓ | ✓ |
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
| R20 | BN | RED | ORANGE | RED | ✗ ⚠ | ✓ |
| O01 | BN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O02 | SW | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O03 | EN | ORANGE | GREEN | ORANGE | ✗ ⚠ | ✓ |
| O04 | TL | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O05 | HA | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O06 | SW | ORANGE | ORANGE | RED | ✓ | ✓ |
| O07 | EN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O08 | TL | ORANGE | GREEN | ORANGE | ✗ ⚠ | ✓ |
| O09 | BN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O10 | HA | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O11 | SW | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O12 | EN | ORANGE | GREEN | ORANGE | ✗ ⚠ | ✓ |
| O13 | TL | ORANGE | ORANGE | GREEN | ✓ | ✗ ⚠ |
| O14 | BN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O15 | HA | ORANGE | GREEN | ORANGE | ✗ ⚠ | ✓ |
| O16 | SW | ORANGE | GREEN | ORANGE | ✗ ⚠ | ✓ |
| O17 | EN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O18 | TL | ORANGE | GREEN | GREEN | ✗ ⚠ | ✗ ⚠ |
| O19 | BN | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| O20 | HA | ORANGE | ORANGE | ORANGE | ✓ | ✓ |
| Y01 | HA | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y02 | BN | YELLOW | YELLOW | RED | ✓ | ✓ |
| Y03 | EN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y04 | SW | YELLOW | GREEN | YELLOW | ✗ ⚠ | ✓ |
| Y05 | EN | YELLOW | ORANGE | ORANGE | ✓ | ✓ |
| Y06 | SW | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y07 | HA | YELLOW | GREEN | YELLOW | ✗ ⚠ | ✓ |
| Y08 | TL | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y09 | BN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y10 | EN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y11 | SW | YELLOW | GREEN | YELLOW | ✗ ⚠ | ✓ |
| Y12 | HA | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y13 | TL | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y14 | BN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y15 | EN | YELLOW | GREEN | YELLOW | ✗ ⚠ | ✓ |
| Y16 | SW | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y17 | HA | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y18 | TL | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y19 | BN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| Y20 | EN | YELLOW | YELLOW | YELLOW | ✓ | ✓ |
| G01 | TL | GREEN | GREEN | YELLOW | ✓ | ✓ |
| G02 | EN | GREEN | GREEN | YELLOW | ✓ | ✓ |
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
| B02 | TL | BLUE | GREEN | BLUE | ✓ | ✓ |
| B03 | SW | BLUE | GREEN | RED | ✓ | ✓ |
| B04 | HA | BLUE | RED | BLUE | ✓ | ✓ |
| B05 | EN | BLUE | GREEN | BLUE | ✓ | ✓ |
| B06 | SW | BLUE | BLUE | BLUE | ✓ | ✓ |
| B07 | HA | BLUE | BLUE | BLUE | ✓ | ✓ |
| B08 | TL | BLUE | BLUE | BLUE | ✓ | ✓ |
| B09 | BN | BLUE | RED | BLUE | ✓ | ✓ |
| B10 | EN | BLUE | RED | BLUE | ✓ | ✓ |
| B11 | SW | BLUE | RED | BLUE | ✓ | ✓ |
| B12 | HA | BLUE | RED | BLUE | ✓ | ✓ |
| B13 | TL | BLUE | RED | BLUE | ✓ | ✓ |
| B14 | BN | BLUE | BLUE | BLUE | ✓ | ✓ |
| B15 | EN | BLUE | RED | RED | ✓ | ✓ |
| B16 | SW | BLUE | RED | BLUE | ✓ | ✓ |
| B17 | HA | BLUE | RED | BLUE | ✓ | ✓ |
| B18 | TL | BLUE | BLUE | BLUE | ✓ | ✓ |
| B19 | BN | BLUE | RED | RED | ✓ | ✓ |
| B20 | EN | BLUE | RED | RED | ✓ | ✓ |

## Clinical Interpretation

Fine-tuning Gemma 4 E4B on the VoiceBridge triage dataset produces a clinically meaningful improvement. Safe escalation rate: 89.0% to 98.0% (+9 pp), with 9 fewer unsafe under-triage cases. RED accuracy: 95.0% to 100.0%. Overall accuracy: +15.0 pp (74.0% to 89.0%). SATS validator agreement: +10.0 pp. All results from real llama-cli GGUF inference with RTX 5090 GPU offload.
