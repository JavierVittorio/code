# Scorecard - dev-v2-prompt

model `google/gemma-4-31b-it` | prompt `v2` | images `optimized` | config `109fd69d4e6e` | git `ef78f95` | dataset `9f2bcacf0589` (53 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **95.0%** | labeled fields whose final answer is right (incl. correct 'absent') |
| precision of emitted values | **95.1%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 100.0% | fields not abstained / failed |
| miss rate | 0.5% | said 'absent' but the field is printed |
| wrong-value rate | 4.9% | emitted a value that does not match (near-miss share 25.9%) |
| abstention precision | - | abstentions that prevented an error |
| docs with every field correct | 67.9% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **81.1%**; of those, fully correct: **74.4%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 66.7%

## Failure taxonomy

| outcome | count |
|---|---|
| correct | 523 |
| correct_absent | 50 |
| missed | 3 |
| wrong | 27 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_number | 53 | 92.5% | 94.1% | 0.0% | 1.9% | 5.8% | 0.0% | missed:1, wrong:3 |
| invoice_date | 53 | 83.0% | 83.0% | - | 0.0% | 17.0% | 0.0% | wrong:9 |
| due_date | 47 | 91.5% | 90.7% | 0.0% | 0.0% | 9.3% | 0.0% | wrong:4 |
| currency | 53 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| po_number | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 53 | 98.1% | 100.0% | - | 1.9% | 0.0% | 0.0% | missed:1 |
| vendor_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_tax_id | 12 | 91.7% | 88.9% | 0.0% | 0.0% | 11.1% | 0.0% | wrong:1 |
| bill_to_name | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| bill_to_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 53 | 94.3% | 94.3% | - | 0.0% | 5.7% | 0.0% | wrong:3 |
| discount | 12 | 91.7% | 75.0% | 0.0% | 0.0% | 25.0% | 0.0% | wrong:1 |
| other_charges | 12 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| tax_amount | 53 | 94.3% | 96.2% | - | 1.9% | 3.8% | 0.0% | missed:1, wrong:2 |
| total | 53 | 92.5% | 92.5% | - | 0.0% | 7.5% | 0.0% | wrong:4 |

## Line items

53 docs, 626 GT rows, 629 predicted. Row P/R/F1 (all labeled cells correct): 94.1% / 94.6% / 94.3%. Row count exact: 96.2%. Cell accuracy: description 97.4%, amount 97.8%, quantity 96.8%, unit_price 97.4%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 200 | 97.5% | 96.8% | 0.0% | 0.0% |
| clean | 44 | 97.7% | 97.7% | - | 0.0% |
| credit | 16 | 100.0% | 100.0% | - | 0.0% |
| currency | 27 | 92.6% | 96.2% | - | 0.0% |
| decoy_amounts | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| freight | 18 | 94.4% | 94.4% | - | 0.0% |
| handwritten | 26 | 96.2% | 96.2% | - | 0.0% |
| hard | 44 | 95.5% | 95.3% | 0.0% | 0.0% |
| image | 243 | 91.4% | 91.3% | 0.0% | 0.0% |
| locale:EU | 60 | 95.0% | 93.5% | 0.0% | 0.0% |
| locale:ID | 60 | 96.7% | 95.9% | 0.0% | 0.0% |
| locale:UK | 40 | 100.0% | 100.0% | 0.0% | 0.0% |
| locale:US | 80 | 98.8% | 98.5% | 0.0% | 0.0% |
| multipage | 125 | 95.2% | 94.7% | 0.0% | 0.0% |
| photo | 72 | 81.9% | 84.3% | - | 0.0% |
| scan | 45 | 95.6% | 95.6% | - | 0.0% |
| scan:heavy | 40 | 90.0% | 87.5% | 0.0% | 0.0% |
| scan:light | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| ship_to | 120 | 98.3% | 98.1% | 0.0% | 0.0% |
| should_flag | 27 | 92.6% | 92.6% | - | 0.0% |
| source:ipp-benchmark-v1 | 363 | 93.4% | 94.2% | 0.0% | 0.0% |
| source:synthetic | 240 | 97.5% | 96.9% | 0.0% | 0.0% |
| synthetic | 240 | 97.5% | 96.9% | 0.0% | 0.0% |
| table_split | 80 | 95.0% | 94.2% | 0.0% | 0.0% |
| tax | 26 | 100.0% | 100.0% | - | 0.0% |

## Confidence calibration (all docs)

n=550 proposed values, base accuracy 95.1%, ECE **0.033**, AUROC fused **0.7032** vs model self-confidence 0.6578

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.7-0.8 | 2 | 0.748 | 0.0% |
| 0.8-0.9 | 4 | 0.842 | 25.0% |
| 0.9-1.0 | 544 | 0.986 | 96.0% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 96.0% | 0.987 |
| 70.0% | 97.1% | 0.982 |
| 80.0% | 97.5% | 0.982 |
| 90.0% | 97.6% | 0.979 |
| 95.0% | 96.4% | 0.967 |
| 100.0% | 95.1% | 0.741 |

## Confidence calibration (held-out test split)

n=290 proposed values, base accuracy 94.5%, ECE **0.0391**, AUROC fused **0.772** vs model self-confidence 0.602

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.7-0.8 | 2 | 0.748 | 0.0% |
| 0.8-0.9 | 1 | 0.841 | 0.0% |
| 0.9-1.0 | 287 | 0.986 | 95.5% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 97.2% | 0.987 |
| 70.0% | 97.5% | 0.982 |
| 80.0% | 97.8% | 0.982 |
| 90.0% | 98.1% | 0.981 |
| 95.0% | 96.0% | 0.969 |
| 100.0% | 94.5% | 0.741 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | 0 | 23,963 ms | 105,988 ms | 1.3962 | 26.4% | 13.2% | 4,892 | 2,536 | $0.202953 | $1.3024 | 6.57 docs/min |

