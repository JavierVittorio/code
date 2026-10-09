# Scorecard - final-v3.2-real

model `google/gemma-4-31b-it` | prompt `v3` | images `raw` | config `d4f9e6f3eed5` | git `0ef047f` | dataset `b24194a50019` (70 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **88.1%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 91.3% | extraction quality independent of the abstain threshold |
| precision of emitted values | **95.5%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 94.1% | fields not abstained / failed |
| miss rate | 2.3% | said 'absent' but the field is printed |
| wrong-value rate | 4.1% | emitted a value that does not match (near-miss share 40.0%) |
| abstention precision | 45.6% | abstentions that prevented an error |
| docs with every field correct | 51.4% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **61.4%**; of those, fully correct: **74.4%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 100.0%

## Failure taxonomy

| outcome | count |
|---|---|
| abstained_lost | 25 |
| abstained_saved | 21 |
| correct | 641 |
| correct_absent | 51 |
| missed | 17 |
| wrong | 30 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 70 | 98.6% | 100.0% | - | 0.0% | 0.0% | 1.4% | abstained_lost:1 |
| invoice_number | 70 | 72.9% | 79.4% | 0.0% | 4.3% | 18.8% | 4.3% | abstained_saved:3, missed:3, wrong:13 |
| invoice_date | 70 | 91.4% | 94.1% | - | 1.4% | 5.7% | 1.4% | abstained_saved:1, missed:1, wrong:4 |
| due_date | 47 | 95.7% | 100.0% | 0.0% | 0.0% | 0.0% | 4.3% | abstained_lost:1, abstained_saved:1 |
| currency | 70 | 98.6% | 100.0% | - | 0.0% | 0.0% | 1.4% | abstained_lost:1 |
| po_number | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 70 | 95.7% | 98.5% | - | 0.0% | 1.4% | 2.9% | abstained_lost:2, wrong:1 |
| vendor_address | 12 | 91.7% | 100.0% | - | 0.0% | 0.0% | 8.3% | abstained_lost:1 |
| vendor_tax_id | 28 | 75.0% | 81.8% | 0.0% | 0.0% | 16.0% | 10.7% | abstained_saved:3, wrong:4 |
| bill_to_name | 27 | 85.2% | 91.7% | 0.0% | 0.0% | 7.7% | 7.4% | abstained_saved:2, wrong:2 |
| bill_to_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 68 | 80.9% | 93.2% | - | 0.0% | 5.9% | 13.2% | abstained_lost:4, abstained_saved:5, wrong:4 |
| discount | 13 | 84.6% | 100.0% | 0.0% | 0.0% | 0.0% | 15.4% | abstained_lost:1, abstained_saved:1 |
| other_charges | 12 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 28 | 50.0% | 100.0% | 0.0% | 44.4% | 0.0% | 7.1% | abstained_lost:2, missed:12 |
| tax_amount | 70 | 81.4% | 96.6% | - | 1.4% | 2.9% | 14.3% | abstained_lost:9, abstained_saved:1, missed:1, wrong:2 |
| total | 70 | 90.0% | 100.0% | - | 0.0% | 0.0% | 10.0% | abstained_lost:3, abstained_saved:4 |

## Line items

69 docs, 664 GT rows, 667 predicted. Row P/R/F1 (all labeled cells correct): 91.6% / 92.0% / 91.8%. Row count exact: 97.1%. Cell accuracy: description 96.7%, amount 97.0%, quantity 92.4%, unit_price 95.5%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 200 | 95.0% | 98.6% | 0.0% | 4.0% |
| clean | 44 | 100.0% | 100.0% | - | 0.0% |
| credit | 16 | 100.0% | 100.0% | - | 0.0% |
| currency | 27 | 92.6% | 96.2% | - | 0.0% |
| decoy_amounts | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| faded | 22 | 50.0% | 84.6% | - | 27.3% |
| freight | 18 | 88.9% | 100.0% | - | 11.1% |
| handwritten | 26 | 88.5% | 92.0% | - | 3.9% |
| hard | 44 | 88.6% | 100.0% | 0.0% | 11.4% |
| image | 243 | 88.9% | 94.2% | 0.0% | 5.8% |
| label_corrected | 33 | 54.5% | 90.0% | - | 27.3% |
| locale:EU | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| locale:ID | 60 | 86.7% | 97.6% | 0.0% | 11.7% |
| locale:UK | 40 | 97.5% | 100.0% | 0.0% | 2.5% |
| locale:US | 80 | 98.8% | 100.0% | 0.0% | 1.2% |
| multipage | 125 | 97.6% | 99.1% | 0.0% | 1.6% |
| non_english | 182 | 70.3% | 88.2% | 0.0% | 12.1% |
| photo | 72 | 79.2% | 87.7% | - | 8.3% |
| real_photo | 182 | 70.3% | 88.2% | 0.0% | 12.1% |
| scan | 45 | 100.0% | 100.0% | - | 0.0% |
| scan:heavy | 40 | 82.5% | 96.2% | 0.0% | 15.0% |
| scan:light | 60 | 96.7% | 97.7% | 0.0% | 1.7% |
| ship_to | 120 | 93.3% | 100.0% | 0.0% | 6.7% |
| should_flag | 27 | 81.5% | 100.0% | - | 18.5% |
| source:invoices-receipts-pt | 182 | 70.3% | 88.2% | 0.0% | 12.1% |
| source:ipp-benchmark-v1 | 363 | 92.3% | 96.8% | 0.0% | 4.1% |
| source:synthetic | 240 | 95.4% | 98.9% | 0.0% | 3.8% |
| synthetic | 240 | 95.4% | 98.9% | 0.0% | 3.8% |
| table_split | 80 | 97.5% | 98.5% | 0.0% | 1.2% |
| tax | 26 | 100.0% | 100.0% | - | 0.0% |
| thermal_receipt | 182 | 70.3% | 88.2% | 0.0% | 12.1% |

## Confidence calibration (all docs)

n=717 proposed values, base accuracy 92.2%, ECE **0.0553**, AUROC fused **0.8111** vs model self-confidence 0.6439

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.1-0.2 | 2 | 0.154 | 0.0% |
| 0.3-0.4 | 1 | 0.378 | 0.0% |
| 0.6-0.7 | 4 | 0.64 | 0.0% |
| 0.8-0.9 | 12 | 0.873 | 83.3% |
| 0.9-1.0 | 698 | 0.984 | 93.3% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 97.2% | 0.984 |
| 70.0% | 97.6% | 0.982 |
| 80.0% | 97.7% | 0.982 |
| 90.0% | 95.8% | 0.967 |
| 95.0% | 94.4% | 0.943 |
| 100.0% | 92.2% | 0.119 |

## Confidence calibration (held-out test split)

n=387 proposed values, base accuracy 91.0%, ECE **0.067**, AUROC fused **0.8973** vs model self-confidence 0.6621

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.1-0.2 | 1 | 0.119 | 0.0% |
| 0.3-0.4 | 1 | 0.378 | 0.0% |
| 0.6-0.7 | 3 | 0.642 | 0.0% |
| 0.8-0.9 | 4 | 0.871 | 75.0% |
| 0.9-1.0 | 378 | 0.984 | 92.3% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 99.0% | 0.988 |
| 70.0% | 98.9% | 0.982 |
| 80.0% | 98.7% | 0.982 |
| 90.0% | 95.4% | 0.967 |
| 95.0% | 93.5% | 0.943 |
| 100.0% | 91.0% | 0.119 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 70 | 0 | 21,209 ms | 41,725 ms | 0.3571 | 44.3% | 2.9% | 568 | 159 | $0.01986 | $0.1053 | 24.4 docs/min |

_53 docs served from response cache (excluded from latency percentiles)._
