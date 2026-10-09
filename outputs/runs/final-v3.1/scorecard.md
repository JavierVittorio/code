# Scorecard - final-v3.1

model `google/gemma-4-31b-it` | prompt `v3` | images `raw` | config `d4f9e6f3eed5` | git `7fc776b` | dataset `9f2bcacf0589` (53 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **93.5%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 95.4% | extraction quality independent of the abstain threshold |
| precision of emitted values | **97.5%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 96.0% | fields not abstained / failed |
| miss rate | 0.4% | said 'absent' but the field is printed |
| wrong-value rate | 2.4% | emitted a value that does not match (near-miss share 69.2%) |
| abstention precision | 54.2% | abstentions that prevented an error |
| docs with every field correct | 66.0% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **64.1%**; of those, fully correct: **91.2%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 100.0%

## Failure taxonomy

| outcome | count |
|---|---|
| abstained_lost | 11 |
| abstained_saved | 13 |
| correct | 514 |
| correct_absent | 50 |
| missed | 2 |
| wrong | 13 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_number | 53 | 88.7% | 93.9% | 0.0% | 1.9% | 5.8% | 3.8% | abstained_saved:2, missed:1, wrong:3 |
| invoice_date | 53 | 90.6% | 92.3% | - | 0.0% | 7.5% | 1.9% | abstained_saved:1, wrong:4 |
| due_date | 47 | 95.7% | 100.0% | 0.0% | 0.0% | 0.0% | 4.3% | abstained_lost:1, abstained_saved:1 |
| currency | 53 | 98.1% | 100.0% | - | 0.0% | 0.0% | 1.9% | abstained_lost:1 |
| po_number | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 53 | 98.1% | 98.1% | - | 0.0% | 1.9% | 0.0% | wrong:1 |
| vendor_address | 12 | 91.7% | 100.0% | - | 0.0% | 0.0% | 8.3% | abstained_lost:1 |
| vendor_tax_id | 12 | 91.7% | 88.9% | 0.0% | 0.0% | 11.1% | 0.0% | wrong:1 |
| bill_to_name | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| bill_to_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 53 | 83.0% | 93.6% | - | 0.0% | 5.7% | 11.3% | abstained_lost:2, abstained_saved:4, wrong:3 |
| discount | 12 | 91.7% | 100.0% | 0.0% | 0.0% | 0.0% | 8.3% | abstained_saved:1 |
| other_charges | 12 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 12 | 91.7% | 100.0% | 0.0% | 0.0% | 0.0% | 8.3% | abstained_lost:1 |
| tax_amount | 53 | 84.9% | 97.8% | - | 1.9% | 1.9% | 11.3% | abstained_lost:5, abstained_saved:1, missed:1, wrong:1 |
| total | 53 | 94.3% | 100.0% | - | 0.0% | 0.0% | 5.7% | abstained_saved:3 |

## Line items

53 docs, 626 GT rows, 629 predicted. Row P/R/F1 (all labeled cells correct): 92.7% / 93.1% / 92.9%. Row count exact: 96.2%. Cell accuracy: description 97.1%, amount 97.0%, quantity 94.2%, unit_price 96.3%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 200 | 95.0% | 98.6% | 0.0% | 4.0% |
| clean | 44 | 100.0% | 100.0% | - | 0.0% |
| credit | 16 | 100.0% | 100.0% | - | 0.0% |
| currency | 27 | 92.6% | 96.2% | - | 0.0% |
| decoy_amounts | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| freight | 18 | 88.9% | 100.0% | - | 11.1% |
| handwritten | 26 | 88.5% | 92.0% | - | 3.9% |
| hard | 44 | 88.6% | 100.0% | 0.0% | 11.4% |
| image | 243 | 88.9% | 94.2% | 0.0% | 5.8% |
| locale:EU | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| locale:ID | 60 | 86.7% | 97.6% | 0.0% | 11.7% |
| locale:UK | 40 | 97.5% | 100.0% | 0.0% | 2.5% |
| locale:US | 80 | 98.8% | 100.0% | 0.0% | 1.2% |
| multipage | 125 | 97.6% | 99.1% | 0.0% | 1.6% |
| photo | 72 | 79.2% | 87.7% | - | 8.3% |
| scan | 45 | 100.0% | 100.0% | - | 0.0% |
| scan:heavy | 40 | 82.5% | 96.2% | 0.0% | 15.0% |
| scan:light | 60 | 96.7% | 97.7% | 0.0% | 1.7% |
| ship_to | 120 | 93.3% | 100.0% | 0.0% | 6.7% |
| should_flag | 27 | 81.5% | 100.0% | - | 18.5% |
| source:ipp-benchmark-v1 | 363 | 92.3% | 96.8% | 0.0% | 4.1% |
| source:synthetic | 240 | 95.4% | 98.9% | 0.0% | 3.8% |
| synthetic | 240 | 95.4% | 98.9% | 0.0% | 3.8% |
| table_split | 80 | 97.5% | 98.5% | 0.0% | 1.2% |
| tax | 26 | 100.0% | 100.0% | - | 0.0% |

## Confidence calibration (all docs)

n=551 proposed values, base accuracy 94.4%, ECE **0.036**, AUROC fused **0.7797** vs model self-confidence 0.572

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.1-0.2 | 2 | 0.154 | 0.0% |
| 0.3-0.4 | 1 | 0.378 | 0.0% |
| 0.6-0.7 | 1 | 0.602 | 0.0% |
| 0.8-0.9 | 3 | 0.862 | 33.3% |
| 0.9-1.0 | 544 | 0.985 | 95.4% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 97.5% | 0.987 |
| 70.0% | 97.7% | 0.982 |
| 80.0% | 98.0% | 0.982 |
| 90.0% | 97.6% | 0.975 |
| 95.0% | 96.6% | 0.955 |
| 100.0% | 94.4% | 0.119 |

## Confidence calibration (held-out test split)

n=290 proposed values, base accuracy 94.1%, ECE **0.0369**, AUROC fused **0.9337** vs model self-confidence 0.5588

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.1-0.2 | 1 | 0.119 | 0.0% |
| 0.3-0.4 | 1 | 0.378 | 0.0% |
| 0.6-0.7 | 1 | 0.602 | 0.0% |
| 0.8-0.9 | 2 | 0.881 | 50.0% |
| 0.9-1.0 | 285 | 0.985 | 95.4% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 100.0% | 0.988 |
| 70.0% | 99.5% | 0.982 |
| 80.0% | 99.1% | 0.982 |
| 90.0% | 98.5% | 0.975 |
| 95.0% | 96.4% | 0.95 |
| 100.0% | 94.1% | 0.119 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | 0 | - ms | - ms | 0.0 | 43.4% | 3.8% | 0.0 | 0.0 | $0.0 | $0.0 | 35.48 docs/min |

_53 docs served from response cache (excluded from latency percentiles)._
