# Regression report: `dev-v1-baseline` -> `dev-v2-prompt`

**PASS**

| | baseline | candidate |
|---|---|---|
| model | `google/gemma-4-31b-it` | `google/gemma-4-31b-it` |
| prompt_version | `v1` | `v2` |
| image_profile | `optimized` | `optimized` |
| config_fingerprint | `109fd69d4e6e` | `109fd69d4e6e` |
| git_sha | `eb2db7f` | `ef78f95` |

| metric | baseline | candidate | delta |
|---|---|---|---|
| accuracy | 93.9% | 95.0% | +1.2 pts |
| precision | 94.9% | 95.1% | +0.2 pts |
| hallucination_rate | 2.0% | 0.0% | -2.0 pts |
| coverage | 100.0% | 100.0% | +0.0 pts |
| miss_rate | 1.6% | 0.5% | -1.1 pts |
| wrong_rate | 4.9% | 4.9% | +0.0 pts |
| doc_all_fields_correct | 62.3% | 67.9% | +5.7 pts |
| line-item row F1 | 92.6% | 94.3% | |
| p95 latency | 105583.5 ms | 105987.8 ms | |
| input tokens/doc | 3409.9245 | 4892.0566 | |
| list $/1k docs | 1.0829 | 1.3024 | |

Paired bootstrap over documents (accuracy delta): +1.16 pts, 95% CI [-0.17, +2.56]

## Per field

| field | n | baseline | candidate | delta pts | hallucination |
|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | +0.0 | - -> - |
| invoice_number | 53 | 90.6% | 92.5% | +1.9 | 100.0% -> 0.0% |
| invoice_date | 53 | 86.8% | 83.0% | -3.8 | - -> - |
| due_date | 47 | 91.5% | 91.5% | +0.0 | 0.0% -> 0.0% |
| currency | 53 | 86.8% | 100.0% | +13.2 | - -> - |
| po_number | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| payment_terms | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| vendor_name | 53 | 98.1% | 98.1% | +0.0 | - -> - |
| vendor_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| vendor_tax_id | 12 | 91.7% | 91.7% | +0.0 | 0.0% -> 0.0% |
| bill_to_name | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| bill_to_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| ship_to_name | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| ship_to_address | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| subtotal | 53 | 92.5% | 94.3% | +1.9 | - -> - |
| discount | 12 | 91.7% | 91.7% | +0.0 | 0.0% -> 0.0% |
| other_charges | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_rate | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_amount | 53 | 94.3% | 94.3% | +0.0 | - -> - |
| total | 53 | 92.5% | 92.5% | +0.0 | - -> - |

## Flips: 4 newly wrong, 11 newly right

| doc | field | new outcome | gt | candidate value | conf |
|---|---|---|---|---|---|
| ipp-freight-clearing-na-1 | invoice_date | wrong | 2026-08-02 | 2026-02-08 | 0.996 |
| ipp-hard-total-inflated | total | wrong | 21430.46 | 18008.79 | 0.832 |
| ipp-multipage-2p-us-2 | invoice_date | wrong | 2026-05-11 | 2006-05-11 | 0.991 |
| ipp-multipage-2p-us-2 | due_date | wrong | 2026-07-10 | 2006-10-07 | 0.98 |
