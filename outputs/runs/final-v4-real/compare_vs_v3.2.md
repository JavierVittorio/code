# Regression report: `final-v3.2-real` -> `final-v4-real`

**PASS** (1 warnings)

| | baseline | candidate |
|---|---|---|
| model | `google/gemma-4-31b-it` | `google/gemma-4-31b-it` |
| prompt_version | `v3` | `v4` |
| image_profile | `raw` | `raw` |
| config_fingerprint | `d4f9e6f3eed5` | `d4f9e6f3eed5` |
| git_sha | `0ef047f` | `0ef047f` |

| metric | baseline | candidate | delta |
|---|---|---|---|
| raw_accuracy | 91.3% | 93.2% | +1.9 pts |
| accuracy | 88.1% | 89.7% | +1.5 pts |
| precision | 95.5% | 96.6% | +1.1 pts |
| hallucination_rate | 0.0% | 0.0% | +0.0 pts |
| coverage | 94.1% | 93.9% | -0.3 pts |
| miss_rate | 2.3% | 1.4% | -1.0 pts |
| wrong_rate | 4.1% | 3.1% | -1.0 pts |
| doc_all_fields_correct | 51.4% | 54.3% | +2.9 pts |
| line-item row F1 | 91.8% | 91.7% | |
| p95 latency | 41724.9 ms | 61350.6 ms | |
| input tokens/doc | 568.4143 | 3094.1 | |
| list $/1k docs | 0.1053 | 0.7227 | |

Paired bootstrap over documents (accuracy delta): +1.91 pts, 95% CI [+0.64, +3.39]

## Warnings
- cost/1k docs $0.1053 -> $0.7227

## Per field

| field | n | baseline raw acc | candidate raw acc | delta pts | hallucination |
|---|---|---|---|---|---|
| document_type | 70 | 100.0% | 100.0% | +0.0 | - -> - |
| invoice_number | 70 | 72.9% | 77.1% | +4.3 | 0.0% -> 0.0% |
| invoice_date | 70 | 91.4% | 90.0% | -1.4 | - -> - |
| due_date | 47 | 97.9% | 95.7% | -2.1 | 0.0% -> 0.0% |
| currency | 70 | 100.0% | 100.0% | +0.0 | - -> - |
| po_number | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| payment_terms | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| vendor_name | 70 | 98.6% | 95.7% | -2.9 | - -> - |
| vendor_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| vendor_tax_id | 28 | 75.0% | 75.0% | +0.0 | 0.0% -> 0.0% |
| bill_to_name | 27 | 85.2% | 88.9% | +3.7 | 0.0% -> 0.0% |
| bill_to_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| ship_to_name | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| ship_to_address | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| subtotal | 68 | 86.8% | 92.7% | +5.9 | - -> - |
| discount | 13 | 92.3% | 100.0% | +7.7 | 0.0% -> 0.0% |
| other_charges | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_rate | 28 | 57.1% | 85.7% | +28.6 | 0.0% -> 0.0% |
| tax_amount | 70 | 94.3% | 97.1% | +2.9 | - -> - |
| total | 70 | 94.3% | 94.3% | +0.0 | - -> - |

## Flips (end-to-end outcome): 6 newly not-correct, 18 newly right

| doc | field | new outcome | gt | candidate value | conf |
|---|---|---|---|---|---|
| ipp-clean-fr-right-header | due_date | abstained_saved | 2026-04-08 | 2026-04-06 | 0.839 |
| ipp-photo-orientation-moderate | invoice_date | wrong | 2025-12-06 | 2025-06-12 | 0.996 |
| ipp-photo-perspective-severe | currency | abstained_lost | ZAR | ZAR | 0.937 |
| pt-20210324_162353 | total | abstained_saved | 22.45 | 26.66 | 0.299 |
| pt-20210324_195741 | vendor_tax_id | wrong | 500563381 | 510776914 | 0.992 |
| pt-20210429_220319 | vendor_name | abstained_saved | Consertos Rapidos Amoreiras, Lda | Transportes Rapidos Amoreiras, Lda | 0.95 |
