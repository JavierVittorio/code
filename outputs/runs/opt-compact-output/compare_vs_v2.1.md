# Regression report: `dev-v2.1-checks` -> `opt-compact-output`

**PASS**

| | baseline | candidate |
|---|---|---|
| model | `google/gemma-4-31b-it` | `google/gemma-4-31b-it` |
| prompt_version | `v2` | `v2` |
| image_profile | `optimized` | `optimized` |
| config_fingerprint | `daf01b1ce98b` | `a546d4253a34` |
| git_sha | `ef78f95` | `7fc776b` |

| metric | baseline | candidate | delta |
|---|---|---|---|
| accuracy | 95.9% | 95.7% | -0.2 pts |
| precision | 96.0% | 96.2% | +0.2 pts |
| hallucination_rate | 0.0% | 0.0% | +0.0 pts |
| coverage | 100.0% | 100.0% | +0.0 pts |
| miss_rate | 0.5% | 0.9% | +0.4 pts |
| wrong_rate | 4.0% | 3.8% | -0.2 pts |
| doc_all_fields_correct | 75.5% | 73.6% | -1.9 pts |
| line-item row F1 | 94.3% | 94.0% | |
| p95 latency | None ms | 89976.4 ms | |
| input tokens/doc | 5027.1887 | 2693.2642 | |
| list $/1k docs | 1.3156 | 0.7176 | |

Paired bootstrap over documents (accuracy delta): -0.17 pts, 95% CI [-1.23, +0.96]

## Per field

| field | n | baseline | candidate | delta pts | hallucination |
|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 98.1% | -1.9 | - -> - |
| invoice_number | 53 | 92.5% | 92.5% | +0.0 | 0.0% -> 0.0% |
| invoice_date | 53 | 88.7% | 88.7% | +0.0 | - -> - |
| due_date | 47 | 93.6% | 95.7% | +2.1 | 0.0% -> 0.0% |
| currency | 53 | 100.0% | 96.2% | -3.8 | - -> - |
| po_number | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| payment_terms | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| vendor_name | 53 | 98.1% | 98.1% | +0.0 | - -> - |
| vendor_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| vendor_tax_id | 12 | 91.7% | 83.3% | -8.3 | 0.0% -> 0.0% |
| bill_to_name | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| bill_to_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| ship_to_name | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| ship_to_address | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| subtotal | 53 | 94.3% | 96.2% | +1.9 | - -> - |
| discount | 12 | 91.7% | 91.7% | +0.0 | 0.0% -> 0.0% |
| other_charges | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_rate | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_amount | 53 | 94.3% | 94.3% | +0.0 | - -> - |
| total | 53 | 94.3% | 96.2% | +1.9 | - -> - |

## Flips: 5 newly wrong, 4 newly right

| doc | field | new outcome | gt | candidate value | conf |
|---|---|---|---|---|---|
| ipp-clean-us-shipping-and-discount | invoice_date | wrong | 2024-03-05 | 2024-05-03 | 0.984 |
| ipp-credit-brackets-us | currency | missed | USD | None | 0.5 |
| ipp-photo-crop-edges-severe | document_type | missed | invoice | None | 0.5 |
| ipp-photo-motion-blur-severe | currency | missed | GBP | None | 0.5 |
| synth-08-id-heavyscan | vendor_tax_id | wrong | 82.415.903.6-542.000 | 82.415.903.6-542.080 | 0.926 |
