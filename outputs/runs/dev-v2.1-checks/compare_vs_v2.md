# Regression report: `dev-v2-prompt` -> `dev-v2.1-checks`

**PASS**

| | baseline | candidate |
|---|---|---|
| model | `google/gemma-4-31b-it` | `google/gemma-4-31b-it` |
| prompt_version | `v2` | `v2` |
| image_profile | `optimized` | `optimized` |
| config_fingerprint | `109fd69d4e6e` | `daf01b1ce98b` |
| git_sha | `ef78f95` | `ef78f95` |

| metric | baseline | candidate | delta |
|---|---|---|---|
| accuracy | 95.0% | 95.9% | +0.8 pts |
| precision | 95.1% | 96.0% | +0.9 pts |
| hallucination_rate | 0.0% | 0.0% | +0.0 pts |
| coverage | 100.0% | 100.0% | +0.0 pts |
| miss_rate | 0.5% | 0.5% | +0.0 pts |
| wrong_rate | 4.9% | 4.0% | -0.9 pts |
| doc_all_fields_correct | 67.9% | 75.5% | +7.6 pts |
| line-item row F1 | 94.3% | 94.3% | |
| p95 latency | 105987.8 ms | None ms | |
| input tokens/doc | 4892.0566 | 5027.1887 | |
| list $/1k docs | 1.3024 | 1.3156 | |

Paired bootstrap over documents (accuracy delta): +0.83 pts, 95% CI [+0.17, +1.60]

## Per field

| field | n | baseline | candidate | delta pts | hallucination |
|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | +0.0 | - -> - |
| invoice_number | 53 | 92.5% | 92.5% | +0.0 | 0.0% -> 0.0% |
| invoice_date | 53 | 83.0% | 88.7% | +5.7 | - -> - |
| due_date | 47 | 91.5% | 93.6% | +2.1 | 0.0% -> 0.0% |
| currency | 53 | 100.0% | 100.0% | +0.0 | - -> - |
| po_number | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| payment_terms | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| vendor_name | 53 | 98.1% | 98.1% | +0.0 | - -> - |
| vendor_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| vendor_tax_id | 12 | 91.7% | 91.7% | +0.0 | 0.0% -> 0.0% |
| bill_to_name | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| bill_to_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| ship_to_name | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| ship_to_address | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| subtotal | 53 | 94.3% | 94.3% | +0.0 | - -> - |
| discount | 12 | 91.7% | 91.7% | +0.0 | 0.0% -> 0.0% |
| other_charges | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_rate | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_amount | 53 | 94.3% | 94.3% | +0.0 | - -> - |
| total | 53 | 92.5% | 94.3% | +1.9 | - -> - |

## Flips: 0 newly wrong, 5 newly right

