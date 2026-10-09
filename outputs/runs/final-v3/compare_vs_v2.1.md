# Regression report: `dev-v2.1-checks` -> `final-v3`

**FAIL** (1 warnings)

| | baseline | candidate |
|---|---|---|
| model | `google/gemma-4-31b-it` | `google/gemma-4-31b-it` |
| prompt_version | `v2` | `v3` |
| image_profile | `optimized` | `raw` |
| config_fingerprint | `daf01b1ce98b` | `1ee3f156a32b` |
| git_sha | `ef78f95` | `7fc776b` |

| metric | baseline | candidate | delta |
|---|---|---|---|
| accuracy | 95.9% | 91.7% | -4.1 pts |
| precision | 96.0% | 98.2% | +2.2 pts |
| hallucination_rate | 0.0% | 0.0% | +0.0 pts |
| coverage | 100.0% | 93.5% | -6.5 pts |
| miss_rate | 0.5% | 0.4% | -0.2 pts |
| wrong_rate | 4.0% | 1.6% | -2.4 pts |
| doc_all_fields_correct | 75.5% | 56.6% | -18.9 pts |
| line-item row F1 | 94.3% | 92.9% | |
| p95 latency | None ms | 84002.5 ms | |
| input tokens/doc | 5027.1887 | 3059.1509 | |
| list $/1k docs | 1.3156 | 0.7801 | |

Paired bootstrap over documents (accuracy delta): -4.15 pts, 95% CI [-7.01, -1.42]

## Failures
- field accuracy dropped -4.1 pts (95% CI -7.0 .. -1.4)
- field `currency` accuracy 100.0% -> 88.7%
- field `subtotal` accuracy 94.3% -> 81.1%
- field `tax_amount` accuracy 94.3% -> 83.0%

## Warnings
- coverage 100.0% -> 93.5%

## Per field

| field | n | baseline | candidate | delta pts | hallucination |
|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | +0.0 | - -> - |
| invoice_number | 53 | 92.5% | 88.7% | -3.8 | 0.0% -> 0.0% |
| invoice_date | 53 | 88.7% | 86.8% | -1.9 | - -> - |
| due_date | 47 | 93.6% | 93.6% | +0.0 | 0.0% -> 0.0% |
| currency | 53 | 100.0% | 88.7% | -11.3 **FAIL** | - -> - |
| po_number | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| payment_terms | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| vendor_name | 53 | 98.1% | 98.1% | +0.0 | - -> - |
| vendor_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| vendor_tax_id | 12 | 91.7% | 91.7% | +0.0 | 0.0% -> 0.0% |
| bill_to_name | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| bill_to_address | 12 | 100.0% | 100.0% | +0.0 | - -> - |
| ship_to_name | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| ship_to_address | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| subtotal | 53 | 94.3% | 81.1% | -13.2 **FAIL** | - -> - |
| discount | 12 | 91.7% | 91.7% | +0.0 | 0.0% -> 0.0% |
| other_charges | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_rate | 12 | 100.0% | 100.0% | +0.0 | 0.0% -> 0.0% |
| tax_amount | 53 | 94.3% | 83.0% | -11.3 **FAIL** | - -> - |
| total | 53 | 94.3% | 88.7% | -5.7 | - -> - |

## Flips: 33 newly wrong, 8 newly right

| doc | field | new outcome | gt | candidate value | conf |
|---|---|---|---|---|---|
| ipp-currency-nad-bare-dollar | currency | abstained_lost | NAD | NAD | 0.821 |
| ipp-freight-clearing-na-1 | subtotal | abstained_saved | 16655.5 | 16655.00 | 0.446 |
| ipp-freight-clearing-na-1 | tax_amount | abstained_lost | 619.17 | 619.17 | 0.83 |
| ipp-handwritten-invoice-book-average-4 | invoice_date | abstained_lost | 2026-05-16 | 2026-05-16 | 0.922 |
| ipp-handwritten-invoice-book-average-4 | subtotal | abstained_lost | 16252.05 | 16252.05 | 0.922 |
| ipp-handwritten-invoice-book-average-4 | total | abstained_lost | 18689.86 | 18689.86 | 0.911 |
| ipp-handwritten-invoice-book-poor-6 | invoice_number | wrong | 9518 | 958 | 0.931 |
| ipp-handwritten-invoice-book-poor-6 | subtotal | abstained_saved | 6284.61 | 6284.41 | 0.909 |
| ipp-handwritten-invoice-book-poor-6 | total | abstained_lost | 7227.3 | 7227.30 | 0.895 |
| ipp-hard-lines-vs-subtotal | subtotal | abstained_lost | 10661.48 | 10661.48 | 0.83 |
| ipp-hard-lines-vs-subtotal | tax_amount | abstained_lost | 1494.6 | 1494.60 | 0.83 |
| ipp-hard-total-inflated | total | abstained_saved | 21430.46 | 18008.79 | 0.028 |
| ipp-hard-wrong-vat-amount | tax_amount | abstained_lost | 596.64 | 596.64 | 0.83 |
| ipp-multipage-4p-za-5 | subtotal | abstained_lost | 91660.06 | 91660.06 | 0.83 |
| ipp-photo-combo-severe | invoice_number | wrong | IN0099973 | IN009973 | 0.961 |
| ipp-photo-combo-severe | tax_amount | abstained_lost | 1231.26 | 1231.26 | 0.83 |
| ipp-photo-crumple-severe | currency | abstained_lost | GBP | GBP | 0.865 |
| ipp-photo-motion-blur-severe | currency | abstained_lost | GBP | GBP | 0.821 |
| ipp-photo-orientation-moderate | invoice_number | wrong | IN0099973 | IN0009973 | 0.974 |
| ipp-photo-orientation-moderate | tax_amount | abstained_lost | 1231.26 | 1231.26 | 0.83 |
| ipp-scan-grayscale-scan-severe | currency | abstained_lost | GBP | GBP | 0.865 |
| synth-03-id-scan | subtotal | abstained_saved | 156484000.00 | 156484.000 | 0.684 |
| synth-03-id-scan | tax_amount | abstained_saved | 17213240.00 | 17213.240 | 0.684 |
| synth-03-id-scan | total | abstained_saved | 173697240.00 | 173697.240 | 0.694 |
| synth-04-uk-discount | subtotal | abstained_saved | 39665.55 | 39695.55 | 0.482 |
| synth-05-us-multipage | due_date | abstained_saved | 2026-03-22 | 2026-02-22 | 0.482 |
| synth-06-eu-multipage-scan | currency | abstained_lost | EUR | EUR | 0.865 |
| synth-08-id-heavyscan | invoice_date | abstained_lost | 2025-06-10 | 2025-06-10 | 0.906 |
| synth-08-id-heavyscan | due_date | abstained_lost | 2025-07-10 | 2025-07-10 | 0.925 |
| synth-08-id-heavyscan | subtotal | abstained_saved | 125636000.00 | 125636.000 | 0.498 |
| synth-08-id-heavyscan | tax_amount | abstained_saved | 13128962.00 | 13128.962 | 0.487 |
| synth-08-id-heavyscan | total | abstained_saved | 132483162.00 | 132483.162 | 0.498 |
| synth-11-eu-no-tax-id | currency | abstained_lost | EUR | EUR | 0.865 |
