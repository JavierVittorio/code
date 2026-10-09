# Scorecard - dev-v1-baseline

model `google/gemma-4-31b-it` | prompt `v1` | images `optimized` | config `109fd69d4e6e` | git `eb2db7f` | dataset `9f2bcacf0589` (53 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **93.9%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 93.9% | extraction quality independent of the abstain threshold |
| precision of emitted values | **94.9%** | of values we returned, share correct |
| hallucination rate | **2.0%** | values returned for fields verified NOT on the page |
| coverage | 100.0% | fields not abstained / failed |
| miss rate | 1.6% | said 'absent' but the field is printed |
| wrong-value rate | 4.9% | emitted a value that does not match (near-miss share 25.9%) |
| abstention precision | - | abstentions that prevented an error |
| docs with every field correct | 62.3% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **79.2%**; of those, fully correct: **61.9%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 100.0%

## Failure taxonomy

| outcome | count |
|---|---|
| correct | 517 |
| correct_absent | 49 |
| hallucinated | 1 |
| missed | 9 |
| wrong | 27 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_number | 53 | 90.6% | 92.3% | 100.0% | 1.9% | 5.8% | 0.0% | hallucinated:1, missed:1, wrong:3 |
| invoice_date | 53 | 86.8% | 86.8% | - | 0.0% | 13.2% | 0.0% | wrong:7 |
| due_date | 47 | 91.5% | 90.7% | 0.0% | 0.0% | 9.3% | 0.0% | wrong:4 |
| currency | 53 | 86.8% | 95.8% | - | 9.4% | 3.8% | 0.0% | missed:5, wrong:2 |
| po_number | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 53 | 98.1% | 100.0% | - | 1.9% | 0.0% | 0.0% | missed:1 |
| vendor_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_tax_id | 12 | 91.7% | 88.9% | 0.0% | 0.0% | 11.1% | 0.0% | wrong:1 |
| bill_to_name | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| bill_to_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 53 | 92.5% | 94.2% | - | 1.9% | 5.7% | 0.0% | missed:1, wrong:3 |
| discount | 12 | 91.7% | 75.0% | 0.0% | 0.0% | 25.0% | 0.0% | wrong:1 |
| other_charges | 12 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| tax_amount | 53 | 94.3% | 96.2% | - | 1.9% | 3.8% | 0.0% | missed:1, wrong:2 |
| total | 53 | 92.5% | 92.5% | - | 0.0% | 7.5% | 0.0% | wrong:4 |

## Line items

53 docs, 626 GT rows, 629 predicted. Row P/R/F1 (all labeled cells correct): 92.4% / 92.8% / 92.6%. Row count exact: 94.3%. Cell accuracy: description 96.8%, amount 96.0%, quantity 95.2%, unit_price 94.7%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 200 | 97.5% | 96.8% | 0.0% | 0.0% |
| clean | 44 | 95.5% | 97.7% | - | 0.0% |
| credit | 16 | 93.8% | 100.0% | - | 0.0% |
| currency | 27 | 81.5% | 84.6% | - | 0.0% |
| decoy_amounts | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| freight | 18 | 100.0% | 100.0% | - | 0.0% |
| handwritten | 26 | 96.2% | 96.2% | - | 0.0% |
| hard | 44 | 95.5% | 95.5% | 100.0% | 0.0% |
| image | 243 | 89.7% | 90.7% | 0.0% | 0.0% |
| locale:EU | 60 | 95.0% | 93.5% | 0.0% | 0.0% |
| locale:ID | 60 | 96.7% | 95.9% | 0.0% | 0.0% |
| locale:UK | 40 | 100.0% | 100.0% | 0.0% | 0.0% |
| locale:US | 80 | 98.8% | 98.5% | 0.0% | 0.0% |
| multipage | 125 | 96.8% | 96.5% | 0.0% | 0.0% |
| photo | 72 | 76.4% | 82.1% | - | 0.0% |
| scan | 45 | 95.6% | 95.6% | - | 0.0% |
| scan:heavy | 40 | 90.0% | 87.5% | 0.0% | 0.0% |
| scan:light | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| ship_to | 120 | 98.3% | 98.1% | 0.0% | 0.0% |
| should_flag | 27 | 96.3% | 96.3% | - | 0.0% |
| source:ipp-benchmark-v1 | 363 | 91.5% | 93.8% | 100.0% | 0.0% |
| source:synthetic | 240 | 97.5% | 96.9% | 0.0% | 0.0% |
| synthetic | 240 | 97.5% | 96.9% | 0.0% | 0.0% |
| table_split | 80 | 95.0% | 94.2% | 0.0% | 0.0% |
| tax | 26 | 96.2% | 100.0% | - | 0.0% |

## Confidence calibration (all docs)

n=545 proposed values, base accuracy 94.9%, ECE **0.0354**, AUROC fused **0.6686** vs model self-confidence 0.5172

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.7-0.8 | 1 | 0.754 | 0.0% |
| 0.8-0.9 | 4 | 0.854 | 50.0% |
| 0.9-1.0 | 540 | 0.985 | 95.4% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 95.6% | 0.982 |
| 70.0% | 96.6% | 0.982 |
| 80.0% | 97.0% | 0.982 |
| 90.0% | 97.1% | 0.979 |
| 95.0% | 96.1% | 0.964 |
| 100.0% | 94.9% | 0.754 |

## Confidence calibration (held-out test split)

n=288 proposed values, base accuracy 94.1%, ECE **0.0439**, AUROC fused **0.73** vs model self-confidence 0.5055

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.7-0.8 | 1 | 0.754 | 0.0% |
| 0.8-0.9 | 1 | 0.841 | 0.0% |
| 0.9-1.0 | 286 | 0.986 | 94.8% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 96.5% | 0.987 |
| 70.0% | 96.5% | 0.982 |
| 80.0% | 97.0% | 0.982 |
| 90.0% | 97.3% | 0.981 |
| 95.0% | 96.0% | 0.969 |
| 100.0% | 94.1% | 0.754 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | 0 | 29,668 ms | 105,584 ms | 1.3019 | 30.2% | 0.0% | 3,410 | 2,282 | $0.193796 | $1.0829 | 5.8 docs/min |

