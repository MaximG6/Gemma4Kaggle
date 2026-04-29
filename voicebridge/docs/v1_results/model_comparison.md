# VoiceBridge — Base vs Fine-tuned Model Comparison

Benchmark: 20 cases (4 per SATS level), 5 languages (sw, tl, ha, bn, en). Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload (-ngl 99).

## Overall Metrics

| Metric | Fine-tuned VoiceBridge |
|--------|:----------------------:|
| Exact match accuracy      | 76.0% |
| Safe escalation rate      | 93.0% |
| Unsafe under-triage cases | 7 |
| SATS validator agreement  | 84.0% |

## Per-Level Accuracy

| SATS Level | n/N | Accuracy |
|------------|:---:|:--------:|
| RED    | 18/20 | 90.0% |
| ORANGE | 14/20 | 70.0% |
| YELLOW | 15/20 | 75.0% |
| GREEN  | 17/20 | 85.0% |
| BLUE   | 12/20 | 60.0% |

## Per-Language Accuracy

| Language | n/N | Accuracy |
|----------|:---:|:--------:|
| Bengali | 17/18 | 94.4% |
| English | 15/22 | 68.2% |
| Hausa | 16/20 | 80.0% |
| Swahili | 14/21 | 66.7% |
| Tagalog | 14/19 | 73.7% |

## Inference Latency (Fine-tuned, llama-cli + RTX 5090)

| Metric | Value |
|--------|------:|
| mean_s | 5.91s |
| median_s | 5.83s |
| p50_s | 5.84s |
| p95_s | 7.69s |
| min_s | 2.77s |
| max_s | 8.32s |

## Per-Case Results

| ID | Lang | Expected | Predicted | Correct | Safe | Validator |
|----|------|----------|-----------|:-------:|:----:|:---------:|
| R01 | SW | RED | RED | ✓ | ✓ | ✓ |
| R02 | TL | RED | RED | ✓ | ✓ | ✓ |
| R03 | HA | RED | RED | ✓ | ✓ | ✓ |
| R04 | EN | RED | RED | ✓ | ✓ | ✓ |
| R05 | BN | RED | RED | ✓ | ✓ | ✓ |
| R06 | HA | RED | RED | ✓ | ✓ | ✓ |
| R07 | TL | RED | RED | ✓ | ✓ | ✓ |
| R08 | EN | RED | RED | ✓ | ✓ | ✓ |
| R09 | SW | RED | RED | ✓ | ✓ | ✓ |
| R10 | BN | RED | RED | ✓ | ✓ | ✓ |
| R11 | TL | RED | RED | ✓ | ✓ | ✓ |
| R12 | HA | RED | RED | ✓ | ✓ | ✓ |
| R13 | EN | RED | RED | ✓ | ✓ | ✓ |
| R14 | SW | RED | BLUE | ✗ | ✗ ⚠ | ✓ |
| R15 | BN | RED | RED | ✓ | ✓ | ✓ |
| R16 | TL | RED | RED | ✓ | ✓ | ✓ |
| R17 | HA | RED | RED | ✓ | ✓ | ✓ |
| R18 | EN | RED | RED | ✓ | ✓ | ✓ |
| R19 | SW | RED | BLUE | ✗ | ✗ ⚠ | ✓ |
| R20 | BN | RED | RED | ✓ | ✓ | ✓ |
| O01 | BN | ORANGE | ORANGE | ✓ | ✓ | ✓ |
| O02 | SW | ORANGE | ORANGE | ✓ | ✓ | ✓ |
| O03 | EN | ORANGE | ORANGE | ✓ | ✓ | ✗ |
| O04 | TL | ORANGE | ORANGE | ✓ | ✓ | ✗ |
| O05 | HA | ORANGE | ORANGE | ✓ | ✓ | ✓ |
| O06 | SW | ORANGE | ORANGE | ✓ | ✓ | ✗ |
| O07 | EN | ORANGE | RED | ✗ | ✓ | ✓ |
| O08 | TL | ORANGE | ORANGE | ✓ | ✓ | ✗ |
| O09 | BN | ORANGE | ORANGE | ✓ | ✓ | ✓ |
| O10 | HA | ORANGE | ORANGE | ✓ | ✓ | ✗ |
| O11 | SW | ORANGE | ORANGE | ✓ | ✓ | ✗ |
| O12 | EN | ORANGE | RED | ✗ | ✓ | ✓ |
| O13 | TL | ORANGE | ORANGE | ✓ | ✓ | ✗ |
| O14 | BN | ORANGE | ORANGE | ✓ | ✓ | ✓ |
| O15 | HA | ORANGE | RED | ✗ | ✓ | ✓ |
| O16 | SW | ORANGE | RED | ✗ | ✓ | ✓ |
| O17 | EN | ORANGE | ORANGE | ✓ | ✓ | ✓ |
| O18 | TL | ORANGE | RED | ✗ | ✓ | ✓ |
| O19 | BN | ORANGE | ORANGE | ✓ | ✓ | ✗ |
| O20 | HA | ORANGE | RED | ✗ | ✓ | ✓ |
| Y01 | HA | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y02 | BN | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y03 | EN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y04 | SW | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y05 | EN | YELLOW | YELLOW | ✓ | ✓ | ✗ |
| Y06 | SW | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y07 | HA | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y08 | TL | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y09 | BN | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y10 | EN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y11 | SW | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y12 | HA | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y13 | TL | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y14 | BN | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y15 | EN | YELLOW | YELLOW | ✓ | ✓ | ✗ |
| Y16 | SW | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y17 | HA | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y18 | TL | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| Y19 | BN | YELLOW | YELLOW | ✓ | ✓ | ✗ |
| Y20 | EN | YELLOW | YELLOW | ✓ | ✓ | ✓ |
| G01 | TL | GREEN | GREEN | ✓ | ✓ | ✓ |
| G02 | EN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G03 | HA | GREEN | GREEN | ✓ | ✓ | ✓ |
| G04 | SW | GREEN | GREEN | ✓ | ✓ | ✓ |
| G05 | SW | GREEN | YELLOW | ✗ | ✓ | ✓ |
| G06 | HA | GREEN | GREEN | ✓ | ✓ | ✓ |
| G07 | TL | GREEN | GREEN | ✓ | ✓ | ✓ |
| G08 | BN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G09 | EN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G10 | SW | GREEN | GREEN | ✓ | ✓ | ✓ |
| G11 | HA | GREEN | GREEN | ✓ | ✓ | ✓ |
| G12 | TL | GREEN | GREEN | ✓ | ✓ | ✓ |
| G13 | BN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G14 | EN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G15 | SW | GREEN | YELLOW | ✗ | ✓ | ✓ |
| G16 | HA | GREEN | GREEN | ✓ | ✓ | ✓ |
| G17 | TL | GREEN | YELLOW | ✗ | ✓ | ✓ |
| G18 | BN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G19 | EN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G20 | SW | GREEN | GREEN | ✓ | ✓ | ✓ |
| B01 | EN | BLUE | BLUE | ✓ | ✓ | ✓ |
| B02 | TL | BLUE | RED | ✗ | ✓ | ✓ |
| B03 | SW | BLUE | BLUE | ✓ | ✓ | ✓ |
| B04 | HA | BLUE | BLUE | ✓ | ✓ | ✓ |
| B05 | EN | BLUE | BLUE | ✓ | ✓ | ✓ |
| B06 | SW | BLUE | BLUE | ✓ | ✓ | ✓ |
| B07 | HA | BLUE | BLUE | ✓ | ✓ | ✓ |
| B08 | TL | BLUE | BLUE | ✓ | ✓ | ✓ |
| B09 | BN | BLUE | BLUE | ✓ | ✓ | ✓ |
| B10 | EN | BLUE | RED | ✗ | ✓ | ✓ |
| B11 | SW | BLUE | RED | ✗ | ✓ | ✓ |
| B12 | HA | BLUE | BLUE | ✓ | ✓ | ✓ |
| B13 | TL | BLUE | RED | ✗ | ✓ | ✓ |
| B14 | BN | BLUE | BLUE | ✓ | ✓ | ✓ |
| B15 | EN | BLUE | RED | ✗ | ✓ | ✓ |
| B16 | SW | BLUE | RED | ✗ | ✓ | ✓ |
| B17 | HA | BLUE | BLUE | ✓ | ✓ | ✓ |
| B18 | TL | BLUE | BLUE | ✓ | ✓ | ✓ |
| B19 | BN | BLUE | RED | ✗ | ✓ | ✓ |
| B20 | EN | BLUE | RED | ✗ | ✓ | ✓ |

## Clinical Interpretation

Fine-tuned VoiceBridge results on 20 SATS-aligned cases: exact-match accuracy 76.0%, safe escalation rate 93.0%, 7 unsafe under-triage case(s), SATS validator agreement 84.0%. Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload.
