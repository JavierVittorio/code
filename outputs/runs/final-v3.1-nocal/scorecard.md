# Scorecard - final-v3.1-nocal

model `google/gemma-4-31b-it` | prompt `v3` | images `raw` | config `eeb5d3fb6f6c` | git `7fc776b` | dataset `9f2bcacf0589` (53 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **95.9%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 95.9% | extraction quality independent of the abstain threshold |
| precision of emitted values | **95.8%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 100.0% | fields not abstained / failed |
| miss rate | 0.4% | said 'absent' but the field is printed |
| wrong-value rate | 4.2% | emitted a value that does not match (near-miss share 52.2%) |
| abstention precision | - | abstentions that prevented an error |
| docs with every field correct | 69.8% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **66.0%**; of those, fully correct: **88.6%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 100.0%

## Failure taxonomy

| outcome | count |
|---|---|
| correct | 528 |
| correct_absent | 50 |
| missed | 2 |
| wrong | 23 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_number | 53 | 88.7% | 90.2% | 0.0% | 1.9% | 9.6% | 0.0% | missed:1, wrong:5 |
| invoice_date | 53 | 90.6% | 90.6% | - | 0.0% | 9.4% | 0.0% | wrong:5 |
| due_date | 47 | 97.9% | 97.7% | 0.0% | 0.0% | 2.3% | 0.0% | wrong:1 |
| currency | 53 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| po_number | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 53 | 98.1% | 98.1% | - | 0.0% | 1.9% | 0.0% | wrong:1 |
| vendor_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_tax_id | 12 | 91.7% | 88.9% | 0.0% | 0.0% | 11.1% | 0.0% | wrong:1 |
| bill_to_name | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| bill_to_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 53 | 90.6% | 90.6% | - | 0.0% | 9.4% | 0.0% | wrong:5 |
| discount | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| other_charges | 12 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| tax_amount | 53 | 94.3% | 96.2% | - | 1.9% | 3.8% | 0.0% | missed:1, wrong:2 |
| total | 53 | 94.3% | 94.3% | - | 0.0% | 5.7% | 0.0% | wrong:3 |

## Line items

53 docs, 626 GT rows, 629 predicted. Row P/R/F1 (all labeled cells correct): 92.7% / 93.1% / 92.9%. Row count exact: 96.2%. Cell accuracy: description 97.1%, amount 97.0%, quantity 94.2%, unit_price 96.3%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 200 | 97.5% | 96.8% | 0.0% | 0.0% |
| clean | 44 | 100.0% | 100.0% | - | 0.0% |
| credit | 16 | 100.0% | 100.0% | - | 0.0% |
| currency | 27 | 92.6% | 96.2% | - | 0.0% |
| decoy_amounts | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| freight | 18 | 94.4% | 94.4% | - | 0.0% |
| handwritten | 26 | 88.5% | 88.5% | - | 0.0% |
| hard | 44 | 95.5% | 95.3% | 0.0% | 0.0% |
| image | 243 | 92.6% | 92.2% | 0.0% | 0.0% |
| locale:EU | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| locale:ID | 60 | 95.0% | 93.9% | 0.0% | 0.0% |
| locale:UK | 40 | 97.5% | 96.7% | 0.0% | 0.0% |
| locale:US | 80 | 98.8% | 98.5% | 0.0% | 0.0% |
| multipage | 125 | 98.4% | 98.2% | 0.0% | 0.0% |
| photo | 72 | 84.7% | 85.9% | - | 0.0% |
| scan | 45 | 100.0% | 100.0% | - | 0.0% |
| scan:heavy | 40 | 92.5% | 90.6% | 0.0% | 0.0% |
| scan:light | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| ship_to | 120 | 96.7% | 96.2% | 0.0% | 0.0% |
| should_flag | 27 | 92.6% | 92.6% | - | 0.0% |
| source:ipp-benchmark-v1 | 363 | 94.8% | 95.3% | 0.0% | 0.0% |
| source:synthetic | 240 | 97.5% | 96.9% | 0.0% | 0.0% |
| synthetic | 240 | 97.5% | 96.9% | 0.0% | 0.0% |
| table_split | 80 | 97.5% | 97.1% | 0.0% | 0.0% |
| tax | 26 | 100.0% | 100.0% | - | 0.0% |

## Confidence calibration (all docs)

n=551 proposed values, base accuracy 94.4%, ECE **0.0231**, AUROC fused **0.8611** vs model self-confidence 0.572

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.0-0.1 | 2 | 0.027 | 0.0% |
| 0.1-0.2 | 1 | 0.139 | 0.0% |
| 0.3-0.4 | 1 | 0.363 | 0.0% |
| 0.4-0.5 | 4 | 0.474 | 0.0% |
| 0.6-0.7 | 1 | 0.668 | 0.0% |
| 0.8-0.9 | 23 | 0.845 | 78.3% |
| 0.9-1.0 | 519 | 0.983 | 96.7% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 99.6% | 0.986 |
| 70.0% | 98.4% | 0.986 |
| 80.0% | 98.2% | 0.983 |
| 90.0% | 97.6% | 0.968 |
| 95.0% | 96.8% | 0.865 |
| 100.0% | 94.4% | 0.025 |

## Confidence calibration (held-out test split)

n=290 proposed values, base accuracy 94.1%, ECE **0.0234**, AUROC fused **0.9221** vs model self-confidence 0.5588

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.0-0.1 | 1 | 0.025 | 0.0% |
| 0.1-0.2 | 1 | 0.139 | 0.0% |
| 0.3-0.4 | 1 | 0.363 | 0.0% |
| 0.4-0.5 | 1 | 0.446 | 0.0% |
| 0.6-0.7 | 1 | 0.668 | 0.0% |
| 0.8-0.9 | 14 | 0.842 | 71.4% |
| 0.9-1.0 | 271 | 0.983 | 97.0% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 99.3% | 0.986 |
| 70.0% | 99.5% | 0.986 |
| 80.0% | 99.6% | 0.983 |
| 90.0% | 98.5% | 0.961 |
| 95.0% | 96.7% | 0.846 |
| 100.0% | 94.1% | 0.025 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | 0 | - ms | - ms | 0.0377 | 43.4% | 3.8% | 59.6981 | 14.1132 | $0.000651 | $0.0102 | 40.01 docs/min |

_53 docs served from response cache (excluded from latency percentiles)._
