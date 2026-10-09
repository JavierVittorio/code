# Regression report: `dev-v2.1-checks` -> `final-v3.1`

**PASS**

| | baseline | candidate |
|---|---|---|
| model | `google/gemma-4-31b-it` | `google/gemma-4-31b-it` |
| prompt_version | `v2` | `v3` |
| image_profile | `optimized` | `raw` |
| config_fingerprint | `daf01b1ce98b` | `d4f9e6f3eed5` |
| git_sha | `ef78f95` | `7fc776b` |

| metric | baseline | candidate | delta |
|---|---|---|---|
| raw_accuracy | 95.9% | 95.4% | -0.5 pts |
| accuracy | 95.9% | 93.5% | -2.3 pts |
| precision | 96.0% | 97.5% | +1.5 pts |
| hallucination_rate | 0.0% | 0.0% | +0.0 pts |
| coverage | 100.0% | 96.0% | -4.0 pts |
| miss_rate | 0.5% | 0.4% | -0.2 pts |
| wrong_rate | 4.0% | 2.4% | -1.6 pts |
| doc_all_fields_correct | 75.5% | 66.0% | -9.4 pts |
| line-item row F1 | 94.3% | 92.9% | |
| p95 latency | None ms | None ms | |
| input tokens/doc | 5027.1887 | 0.0 | |
| list $/1k docs | 1.3156 | 0.0 | |

Paired bootstrap over documents (accuracy delta): -0.50 pts, 95% CI [-2.35, +1.42]

## Per field

| field | n | baseline raw acc | candidate raw acc | delta pts | hallucination |
|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | +0.0 | - -> - |
| invoice_number | 53 | 92.5% | 88.7% | -3.8 | 0.0% -> 0.0% |
| invoice_date | 53 | 88.7% | 90.6% | +1.9 | - -> - |
| due_date | 47 | 93.6% | 97.9% | +4.2 | 0.0% -> 0.0% |
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
| subtotal | 53 | 94.3% | 86.8% | -7.6 | - -> - |
| discount | 12 | 91.7% | 91.7% | +0.0 | 0.0% -> 0.0% |
| other_charges | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_rate | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_amount | 53 | 94.3% | 94.3% | +0.0 | - -> - |
| total | 53 | 94.3% | 94.3% | +0.0 | - -> - |

## Flips (end-to-end outcome): 22 newly not-correct, 8 newly right

| doc | field | new outcome | gt | candidate value | conf |
|---|---|---|---|---|---|
| ipp-freight-clearing-na-1 | subtotal | abstained_saved | 16655.5 | 16655.00 | 0.911 |
| ipp-freight-clearing-na-1 | tax_amount | abstained_lost | 619.17 | 619.17 | 0.943 |
| ipp-handwritten-invoice-book-poor-6 | invoice_number | abstained_saved | 9518 | 958 | 0.934 |
| ipp-handwritten-invoice-book-poor-6 | subtotal | wrong | 6284.61 | 6284.41 | 0.984 |
| ipp-hard-lines-vs-subtotal | subtotal | abstained_lost | 10661.48 | 10661.48 | 0.943 |
| ipp-hard-lines-vs-subtotal | tax_amount | abstained_lost | 1494.6 | 1494.60 | 0.943 |
| ipp-hard-total-inflated | total | abstained_saved | 21430.46 | 18008.79 | 0.19 |
| ipp-hard-wrong-vat-amount | tax_amount | abstained_lost | 596.64 | 596.64 | 0.943 |
| ipp-multipage-4p-za-5 | subtotal | abstained_lost | 91660.06 | 91660.06 | 0.943 |
| ipp-photo-combo-severe | invoice_number | wrong | IN0099973 | IN009973 | 0.96 |
| ipp-photo-combo-severe | tax_amount | abstained_lost | 1231.26 | 1231.26 | 0.943 |
| ipp-photo-motion-blur-severe | currency | abstained_lost | GBP | GBP | 0.937 |
| ipp-photo-orientation-moderate | invoice_number | wrong | IN0099973 | IN0009973 | 0.971 |
| ipp-photo-orientation-moderate | tax_amount | abstained_lost | 1231.26 | 1231.26 | 0.943 |
| synth-03-id-scan | subtotal | abstained_saved | 156484000.00 | 156484.000 | 0.943 |
| synth-04-uk-discount | subtotal | abstained_saved | 39665.55 | 39695.55 | 0.919 |
| synth-05-us-multipage | due_date | abstained_saved | 2026-03-22 | 2026-02-22 | 0.824 |
| synth-08-id-heavyscan | vendor_address | abstained_lost | Jl. Kaliurang Km 9, Sleman, Yogyakarta 55581, Indonesia | Jl. Kalireng Km 9, Sleman, Yogyakarta 55581, Indonesia | 0.943 |
| synth-08-id-heavyscan | subtotal | abstained_saved | 125636000.00 | 125636.000 | 0.602 |
| synth-08-id-heavyscan | tax_rate | abstained_lost | 11 | 11 | 0.881 |
| synth-08-id-heavyscan | tax_amount | abstained_saved | 13128962.00 | 13128.962 | 0.119 |
| synth-08-id-heavyscan | total | abstained_saved | 132483162.00 | 132483.162 | 0.378 |
