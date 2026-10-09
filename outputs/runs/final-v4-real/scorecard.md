# Scorecard - final-v4-real

model `google/gemma-4-31b-it` | prompt `v4` | images `raw` | config `d4f9e6f3eed5` | git `0ef047f` | dataset `b24194a50019` (70 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **89.7%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 93.2% | extraction quality independent of the abstain threshold |
| precision of emitted values | **96.6%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 93.9% | fields not abstained / failed |
| miss rate | 1.4% | said 'absent' but the field is printed |
| wrong-value rate | 3.1% | emitted a value that does not match (near-miss share 39.1%) |
| abstention precision | 41.7% | abstentions that prevented an error |
| docs with every field correct | 54.3% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **58.6%**; of those, fully correct: **80.5%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 100.0%

## Failure taxonomy

| outcome | count |
|---|---|
| abstained_lost | 28 |
| abstained_saved | 20 |
| correct | 653 |
| correct_absent | 51 |
| missed | 10 |
| wrong | 23 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 70 | 98.6% | 100.0% | - | 0.0% | 0.0% | 1.4% | abstained_lost:1 |
| invoice_number | 70 | 77.1% | 82.8% | 0.0% | 4.3% | 15.9% | 2.9% | abstained_saved:2, missed:3, wrong:11 |
| invoice_date | 70 | 90.0% | 92.7% | - | 1.4% | 7.1% | 1.4% | abstained_saved:1, missed:1, wrong:5 |
| due_date | 47 | 93.6% | 100.0% | 0.0% | 0.0% | 0.0% | 6.4% | abstained_lost:1, abstained_saved:2 |
| currency | 70 | 97.1% | 100.0% | - | 0.0% | 0.0% | 2.9% | abstained_lost:2 |
| po_number | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 70 | 94.3% | 100.0% | - | 0.0% | 0.0% | 5.7% | abstained_lost:1, abstained_saved:3 |
| vendor_address | 12 | 91.7% | 100.0% | - | 0.0% | 0.0% | 8.3% | abstained_lost:1 |
| vendor_tax_id | 28 | 75.0% | 78.3% | 0.0% | 0.0% | 20.0% | 7.1% | abstained_saved:2, wrong:5 |
| bill_to_name | 27 | 88.9% | 100.0% | 0.0% | 3.9% | 0.0% | 7.4% | abstained_saved:2, missed:1 |
| bill_to_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 68 | 86.8% | 98.3% | - | 0.0% | 1.5% | 11.8% | abstained_lost:4, abstained_saved:4, wrong:1 |
| discount | 13 | 92.3% | 100.0% | 0.0% | 0.0% | 0.0% | 7.7% | abstained_lost:1 |
| other_charges | 12 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 28 | 71.4% | 100.0% | 0.0% | 14.8% | 0.0% | 14.3% | abstained_lost:4, missed:4 |
| tax_amount | 70 | 82.9% | 98.3% | - | 1.4% | 1.4% | 14.3% | abstained_lost:10, missed:1, wrong:1 |
| total | 70 | 90.0% | 100.0% | - | 0.0% | 0.0% | 10.0% | abstained_lost:3, abstained_saved:4 |

## Line items

69 docs, 664 GT rows, 667 predicted. Row P/R/F1 (all labeled cells correct): 91.5% / 91.9% / 91.7%. Row count exact: 95.7%. Cell accuracy: description 97.1%, amount 97.4%, quantity 92.0%, unit_price 95.5%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 200 | 97.5% | 98.7% | 0.0% | 1.5% |
| clean | 44 | 97.7% | 100.0% | - | 2.3% |
| credit | 16 | 100.0% | 100.0% | - | 0.0% |
| currency | 27 | 96.3% | 100.0% | - | 0.0% |
| decoy_amounts | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| faded | 22 | 50.0% | 84.6% | - | 27.3% |
| freight | 18 | 88.9% | 100.0% | - | 11.1% |
| handwritten | 26 | 92.3% | 96.0% | - | 3.9% |
| hard | 44 | 88.6% | 100.0% | 0.0% | 11.4% |
| image | 243 | 91.0% | 95.7% | 0.0% | 4.9% |
| label_corrected | 33 | 54.5% | 85.7% | - | 24.2% |
| locale:EU | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| locale:ID | 60 | 95.0% | 97.9% | 0.0% | 3.3% |
| locale:UK | 40 | 97.5% | 100.0% | 0.0% | 2.5% |
| locale:US | 80 | 98.8% | 100.0% | 0.0% | 1.2% |
| multipage | 125 | 98.4% | 99.1% | 0.0% | 0.8% |
| non_english | 182 | 73.6% | 90.5% | 0.0% | 14.3% |
| photo | 72 | 77.8% | 90.3% | - | 12.5% |
| real_photo | 182 | 73.6% | 90.5% | 0.0% | 14.3% |
| scan | 45 | 100.0% | 100.0% | - | 0.0% |
| scan:heavy | 40 | 92.5% | 96.7% | 0.0% | 5.0% |
| scan:light | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| ship_to | 120 | 96.7% | 100.0% | 0.0% | 3.3% |
| should_flag | 27 | 81.5% | 100.0% | - | 18.5% |
| source:invoices-receipts-pt | 182 | 73.6% | 90.5% | 0.0% | 14.3% |
| source:ipp-benchmark-v1 | 363 | 92.6% | 98.0% | 0.0% | 5.0% |
| source:synthetic | 240 | 97.5% | 98.9% | 0.0% | 1.7% |
| synthetic | 240 | 97.5% | 98.9% | 0.0% | 1.7% |
| table_split | 80 | 97.5% | 98.5% | 0.0% | 1.2% |
| tax | 26 | 100.0% | 100.0% | - | 0.0% |
| thermal_receipt | 182 | 73.6% | 90.5% | 0.0% | 14.3% |

## Confidence calibration (all docs)

n=724 proposed values, base accuracy 93.7%, ECE **0.0409**, AUROC fused **0.821** vs model self-confidence 0.6692

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.1-0.2 | 1 | 0.19 | 0.0% |
| 0.2-0.3 | 2 | 0.265 | 0.0% |
| 0.6-0.7 | 4 | 0.642 | 50.0% |
| 0.8-0.9 | 11 | 0.87 | 81.8% |
| 0.9-1.0 | 706 | 0.984 | 94.5% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 97.8% | 0.984 |
| 70.0% | 98.2% | 0.982 |
| 80.0% | 98.3% | 0.982 |
| 90.0% | 97.1% | 0.965 |
| 95.0% | 95.6% | 0.943 |
| 100.0% | 93.7% | 0.19 |

## Confidence calibration (held-out test split)

n=391 proposed values, base accuracy 92.8%, ECE **0.0524**, AUROC fused **0.873** vs model self-confidence 0.6722

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.2-0.3 | 2 | 0.265 | 0.0% |
| 0.6-0.7 | 1 | 0.69 | 0.0% |
| 0.8-0.9 | 3 | 0.867 | 100.0% |
| 0.9-1.0 | 385 | 0.984 | 93.5% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 98.5% | 0.988 |
| 70.0% | 98.5% | 0.982 |
| 80.0% | 98.7% | 0.982 |
| 90.0% | 96.9% | 0.967 |
| 95.0% | 94.6% | 0.943 |
| 100.0% | 92.8% | 0.231 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 70 | 0 | 10,755 ms | 61,351 ms | 1.4286 | 42.9% | 0.0% | 3,094 | 1,306 | $0.127328 | $0.7227 | 12.91 docs/min |

