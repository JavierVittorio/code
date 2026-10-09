# Scorecard - final-v3

model `google/gemma-4-31b-it` | prompt `v3` | images `raw` | config `1ee3f156a32b` | git `7fc776b` | dataset `9f2bcacf0589` (53 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **91.7%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 95.0% | extraction quality independent of the abstain threshold |
| precision of emitted values | **98.2%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 93.5% | fields not abstained / failed |
| miss rate | 0.4% | said 'absent' but the field is printed |
| wrong-value rate | 1.6% | emitted a value that does not match (near-miss share 77.8%) |
| abstention precision | 48.7% | abstentions that prevented an error |
| docs with every field correct | 56.6% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **54.7%**; of those, fully correct: **89.7%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 100.0%

## Failure taxonomy

| outcome | count |
|---|---|
| abstained_lost | 20 |
| abstained_saved | 19 |
| correct | 503 |
| correct_absent | 50 |
| missed | 2 |
| wrong | 9 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_number | 53 | 88.7% | 92.0% | 0.0% | 1.9% | 7.7% | 1.9% | abstained_saved:1, missed:1, wrong:4 |
| invoice_date | 53 | 86.8% | 95.8% | - | 0.0% | 3.8% | 9.4% | abstained_lost:2, abstained_saved:3, wrong:2 |
| due_date | 47 | 93.6% | 100.0% | 0.0% | 0.0% | 0.0% | 6.4% | abstained_lost:2, abstained_saved:1 |
| currency | 53 | 88.7% | 100.0% | - | 0.0% | 0.0% | 11.3% | abstained_lost:6 |
| po_number | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 53 | 98.1% | 98.1% | - | 0.0% | 1.9% | 0.0% | wrong:1 |
| vendor_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_tax_id | 12 | 91.7% | 88.9% | 0.0% | 0.0% | 11.1% | 0.0% | wrong:1 |
| bill_to_name | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| bill_to_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 53 | 81.1% | 97.7% | - | 0.0% | 1.9% | 17.0% | abstained_lost:3, abstained_saved:6, wrong:1 |
| discount | 12 | 91.7% | 100.0% | 0.0% | 0.0% | 0.0% | 8.3% | abstained_saved:1 |
| other_charges | 12 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| tax_amount | 53 | 83.0% | 100.0% | - | 1.9% | 0.0% | 15.1% | abstained_lost:5, abstained_saved:3, missed:1 |
| total | 53 | 88.7% | 100.0% | - | 0.0% | 0.0% | 11.3% | abstained_lost:2, abstained_saved:4 |

## Line items

53 docs, 626 GT rows, 629 predicted. Row P/R/F1 (all labeled cells correct): 92.7% / 93.1% / 92.9%. Row count exact: 96.2%. Cell accuracy: description 97.1%, amount 97.0%, quantity 94.2%, unit_price 96.3%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 200 | 93.0% | 98.6% | 0.0% | 6.0% |
| clean | 44 | 100.0% | 100.0% | - | 0.0% |
| credit | 16 | 100.0% | 100.0% | - | 0.0% |
| currency | 27 | 88.9% | 96.0% | - | 3.7% |
| decoy_amounts | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| freight | 18 | 88.9% | 100.0% | - | 11.1% |
| handwritten | 26 | 73.1% | 95.0% | - | 23.1% |
| hard | 44 | 88.6% | 100.0% | 0.0% | 11.4% |
| image | 243 | 84.8% | 95.8% | 0.0% | 11.5% |
| locale:EU | 60 | 95.0% | 97.7% | 0.0% | 3.3% |
| locale:ID | 60 | 83.3% | 97.5% | 0.0% | 15.0% |
| locale:UK | 40 | 97.5% | 100.0% | 0.0% | 2.5% |
| locale:US | 80 | 98.8% | 100.0% | 0.0% | 1.2% |
| multipage | 125 | 96.8% | 99.1% | 0.0% | 2.4% |
| photo | 72 | 77.8% | 91.8% | - | 13.9% |
| scan | 45 | 97.8% | 100.0% | - | 2.2% |
| scan:heavy | 40 | 80.0% | 96.0% | 0.0% | 17.5% |
| scan:light | 60 | 91.7% | 97.6% | 0.0% | 6.7% |
| ship_to | 120 | 93.3% | 100.0% | 0.0% | 6.7% |
| should_flag | 27 | 81.5% | 100.0% | - | 18.5% |
| source:ipp-benchmark-v1 | 363 | 90.4% | 97.9% | 0.0% | 7.2% |
| source:synthetic | 240 | 93.8% | 98.9% | 0.0% | 5.4% |
| synthetic | 240 | 93.8% | 98.9% | 0.0% | 5.4% |
| table_split | 80 | 96.2% | 98.5% | 0.0% | 2.5% |
| tax | 26 | 100.0% | 100.0% | - | 0.0% |

## Confidence calibration (all docs)

n=551 proposed values, base accuracy 94.9%, ECE **0.0169**, AUROC fused **0.9127** vs model self-confidence 0.5866

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.0-0.1 | 1 | 0.028 | 0.0% |
| 0.4-0.5 | 8 | 0.485 | 0.0% |
| 0.6-0.7 | 4 | 0.682 | 0.0% |
| 0.8-0.9 | 18 | 0.842 | 83.3% |
| 0.9-1.0 | 520 | 0.982 | 97.7% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 99.6% | 0.986 |
| 70.0% | 99.2% | 0.984 |
| 80.0% | 98.4% | 0.973 |
| 90.0% | 98.6% | 0.963 |
| 95.0% | 97.7% | 0.865 |
| 100.0% | 94.9% | 0.028 |

## Confidence calibration (held-out test split)

n=290 proposed values, base accuracy 94.1%, ECE **0.0248**, AUROC fused **0.9154** vs model self-confidence 0.5588

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.4-0.5 | 5 | 0.485 | 0.0% |
| 0.6-0.7 | 1 | 0.668 | 0.0% |
| 0.8-0.9 | 12 | 0.839 | 75.0% |
| 0.9-1.0 | 272 | 0.982 | 97.1% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 99.3% | 0.986 |
| 70.0% | 99.5% | 0.984 |
| 80.0% | 98.7% | 0.973 |
| 90.0% | 98.9% | 0.962 |
| 95.0% | 96.7% | 0.846 |
| 100.0% | 94.1% | 0.446 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | 0 | 12,586 ms | 84,002 ms | 1.434 | 45.3% | 3.8% | 3,059 | 1,485 | $0.135717 | $0.7801 | 10.62 docs/min |

_3 docs served from response cache (excluded from latency percentiles)._
