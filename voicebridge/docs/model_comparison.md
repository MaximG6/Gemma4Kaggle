# VoiceBridge — Base vs Fine-tuned Model Comparison

Benchmark: 20 cases (4 per SATS level), 5 languages (sw, tl, ha, bn, en). Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload (-ngl 99).

## Overall Metrics

| Metric | Fine-tuned VoiceBridge |
|--------|:----------------------:|
| Exact match accuracy      | 20.0% |
| Safe escalation rate      | 40.0% |
| Unsafe under-triage cases | 60 |
| SATS validator agreement  | 22.0% |

## Per-Level Accuracy

| SATS Level | n/N | Accuracy |
|------------|:---:|:--------:|
| RED    | 0/20 | 0.0% |
| ORANGE | 0/20 | 0.0% |
| YELLOW | 0/20 | 0.0% |
| GREEN  | 20/20 | 100.0% |
| BLUE   | 0/20 | 0.0% |

## Per-Language Accuracy

| Language | n/N | Accuracy |
|----------|:---:|:--------:|
| Bengali | 3/18 | 16.7% |
| English | 4/22 | 18.2% |
| Hausa | 4/20 | 20.0% |
| Swahili | 5/21 | 23.8% |
| Tagalog | 4/19 | 21.1% |

## Inference Latency (Fine-tuned, llama-cli + RTX 5090)

| Metric | Value |
|--------|------:|
| mean_s | 115.45s |
| median_s | 120.0s |
| p50_s | 120.0s |
| p95_s | 120.0s |
| min_s | 4.78s |
| max_s | 120.0s |

## Per-Case Results

| ID | Lang | Expected | Predicted | Correct | Safe | Validator |
|----|------|----------|-----------|:-------:|:----:|:---------:|
| R01 | SW | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R02 | TL | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R03 | HA | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R04 | EN | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R05 | BN | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R06 | HA | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R07 | TL | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R08 | EN | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R09 | SW | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R10 | BN | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R11 | TL | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R12 | HA | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R13 | EN | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R14 | SW | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R15 | BN | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R16 | TL | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R17 | HA | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R18 | EN | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R19 | SW | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| R20 | BN | RED | GREEN | ✗ | ✗ ⚠ | ✗ |
| O01 | BN | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O02 | SW | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O03 | EN | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O04 | TL | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O05 | HA | ORANGE | GREEN | ✗ | ✗ ⚠ | ✓ |
| O06 | SW | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O07 | EN | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O08 | TL | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O09 | BN | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O10 | HA | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O11 | SW | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O12 | EN | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O13 | TL | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O14 | BN | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O15 | HA | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O16 | SW | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O17 | EN | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O18 | TL | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O19 | BN | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| O20 | HA | ORANGE | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y01 | HA | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y02 | BN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y03 | EN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y04 | SW | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y05 | EN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y06 | SW | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y07 | HA | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y08 | TL | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y09 | BN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y10 | EN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y11 | SW | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y12 | HA | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y13 | TL | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y14 | BN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y15 | EN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y16 | SW | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y17 | HA | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y18 | TL | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y19 | BN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✗ |
| Y20 | EN | YELLOW | GREEN | ✗ | ✗ ⚠ | ✓ |
| G01 | TL | GREEN | GREEN | ✓ | ✓ | ✓ |
| G02 | EN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G03 | HA | GREEN | GREEN | ✓ | ✓ | ✓ |
| G04 | SW | GREEN | GREEN | ✓ | ✓ | ✓ |
| G05 | SW | GREEN | GREEN | ✓ | ✓ | ✓ |
| G06 | HA | GREEN | GREEN | ✓ | ✓ | ✓ |
| G07 | TL | GREEN | GREEN | ✓ | ✓ | ✓ |
| G08 | BN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G09 | EN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G10 | SW | GREEN | GREEN | ✓ | ✓ | ✓ |
| G11 | HA | GREEN | GREEN | ✓ | ✓ | ✓ |
| G12 | TL | GREEN | GREEN | ✓ | ✓ | ✓ |
| G13 | BN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G14 | EN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G15 | SW | GREEN | GREEN | ✓ | ✓ | ✓ |
| G16 | HA | GREEN | GREEN | ✓ | ✓ | ✓ |
| G17 | TL | GREEN | GREEN | ✓ | ✓ | ✓ |
| G18 | BN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G19 | EN | GREEN | GREEN | ✓ | ✓ | ✓ |
| G20 | SW | GREEN | GREEN | ✓ | ✓ | ✓ |
| B01 | EN | BLUE | GREEN | ✗ | ✓ | ✗ |
| B02 | TL | BLUE | GREEN | ✗ | ✓ | ✗ |
| B03 | SW | BLUE | GREEN | ✗ | ✓ | ✗ |
| B04 | HA | BLUE | GREEN | ✗ | ✓ | ✗ |
| B05 | EN | BLUE | GREEN | ✗ | ✓ | ✗ |
| B06 | SW | BLUE | GREEN | ✗ | ✓ | ✗ |
| B07 | HA | BLUE | GREEN | ✗ | ✓ | ✗ |
| B08 | TL | BLUE | GREEN | ✗ | ✓ | ✗ |
| B09 | BN | BLUE | GREEN | ✗ | ✓ | ✗ |
| B10 | EN | BLUE | GREEN | ✗ | ✓ | ✗ |
| B11 | SW | BLUE | GREEN | ✗ | ✓ | ✗ |
| B12 | HA | BLUE | GREEN | ✗ | ✓ | ✗ |
| B13 | TL | BLUE | GREEN | ✗ | ✓ | ✗ |
| B14 | BN | BLUE | GREEN | ✗ | ✓ | ✗ |
| B15 | EN | BLUE | GREEN | ✗ | ✓ | ✗ |
| B16 | SW | BLUE | GREEN | ✗ | ✓ | ✗ |
| B17 | HA | BLUE | GREEN | ✗ | ✓ | ✗ |
| B18 | TL | BLUE | GREEN | ✗ | ✓ | ✗ |
| B19 | BN | BLUE | GREEN | ✗ | ✓ | ✗ |
| B20 | EN | BLUE | GREEN | ✗ | ✓ | ✗ |

## Clinical Interpretation

Fine-tuned VoiceBridge results on 20 SATS-aligned cases: exact-match accuracy 20.0%, safe escalation rate 40.0%, 60 unsafe under-triage case(s), SATS validator agreement 22.0%. Inference via llama-cli Q4_K_M GGUF with RTX 5090 GPU offload.
