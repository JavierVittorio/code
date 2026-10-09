# Regression report: `opt-images-optimized-subset` -> `opt-images-raw-subset`

**PASS**

| | baseline | candidate |
|---|---|---|
| model | `google/gemma-4-31b-it` | `google/gemma-4-31b-it` |
| prompt_version | `v2` | `v2` |
| image_profile | `optimized` | `raw` |
| config_fingerprint | `a546d4253a34` | `eeb5d3fb6f6c` |
| git_sha | `7fc776b` | `7fc776b` |

| metric | baseline | candidate | delta |
|---|---|---|---|
| accuracy | 91.4% | 97.9% | +6.4 pts |
| precision | 90.5% | 97.6% | +7.1 pts |
| hallucination_rate | 0.0% | 0.0% | +0.0 pts |
| coverage | 100.0% | 100.0% | +0.0 pts |
| miss_rate | 0.0% | 0.0% | +0.0 pts |
| wrong_rate | 9.5% | 2.4% | -7.1 pts |
| doc_all_fields_correct | 66.7% | 75.0% | +8.3 pts |
| line-item row F1 | 72.1% | 77.4% | |
| p95 latency | 85434.3 ms | 81528.5 ms | |
| input tokens/doc | 2726.5833 | 2766.5 | |
| list $/1k docs | 0.742 | 0.751 | |

Paired bootstrap over documents (accuracy delta): +6.43 pts, 95% CI [+1.69, +9.88]

## Per field

| field | n | baseline | candidate | delta pts | hallucination |
|---|---|---|---|---|---|
| document_type | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| invoice_number | 12 | 91.7% | 100.0% | +8.3 | - -> - |
| invoice_date | 12 | 83.3% | 83.3% | +0.0 | - -> - |
| due_date | 11 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| currency | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| po_number | 3 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| payment_terms | 3 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| vendor_name | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| vendor_address | 3 | 100.0% | 100.0% | +0.0 | - -> - |
| vendor_tax_id | 3 | 33.3% | 66.7% | +33.3 | - -> - |
| bill_to_name | 3 | 100.0% | 100.0% | +0.0 | - -> - |
| bill_to_address | 3 | 100.0% | 100.0% | +0.0 | - -> - |
| ship_to_name | 3 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| ship_to_address | 3 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| subtotal | 12 | 91.7% | 100.0% | +8.3 | - -> - |
| discount | 3 | 66.7% | 100.0% | +33.3 | 0.0% -> 0.0% |
| other_charges | 3 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_rate | 3 | 100.0% | 100.0% | +0.0 | - -> - |
| tax_amount | 12 | 83.3% | 100.0% | +16.7 | - -> - |
| total | 12 | 75.0% | 100.0% | +25.0 | - -> - |

## Flips: 0 newly wrong, 9 newly right

