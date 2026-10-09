# Scorecard - opt-images-raw-subset

model `google/gemma-4-31b-it` | prompt `v2` | images `raw` | config `eeb5d3fb6f6c` | git `7fc776b` | dataset `bda2917fc309` (12 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **97.9%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 97.9% | extraction quality independent of the abstain threshold |
| precision of emitted values | **97.6%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 100.0% | fields not abstained / failed |
| miss rate | 0.0% | said 'absent' but the field is printed |
| wrong-value rate | 2.4% | emitted a value that does not match (near-miss share 100.0%) |
| abstention precision | - | abstentions that prevented an error |
| docs with every field correct | 75.0% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **91.7%**; of those, fully correct: **72.7%**
- docs whose printed numbers don't reconcile (should be flagged): 0, caught: -

## Failure taxonomy

| outcome | count |
|---|---|
| correct | 123 |
| correct_absent | 14 |
| wrong | 3 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_number | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_date | 12 | 83.3% | 83.3% | - | 0.0% | 16.7% | 0.0% | wrong:2 |
| due_date | 11 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| currency | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| po_number | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_address | 3 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_tax_id | 3 | 66.7% | 66.7% | - | 0.0% | 33.3% | 0.0% | wrong:1 |
| bill_to_name | 3 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| bill_to_address | 3 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| discount | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| other_charges | 3 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 3 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| tax_amount | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| total | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |

## Line items

12 docs, 120 GT rows, 123 predicted. Row P/R/F1 (all labeled cells correct): 76.4% / 78.3% / 77.4%. Row count exact: 83.3%. Cell accuracy: description 81.7%, amount 96.7%, quantity 96.3%, unit_price 94.4%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 60 | 96.7% | 95.7% | 0.0% | 0.0% |
| image | 105 | 97.1% | 96.7% | 0.0% | 0.0% |
| locale:ID | 40 | 97.5% | 96.8% | 0.0% | 0.0% |
| multipage | 29 | 96.5% | 95.8% | 0.0% | 0.0% |
| photo | 18 | 94.4% | 94.4% | - | 0.0% |
| scan | 18 | 100.0% | 100.0% | - | 0.0% |
| scan:heavy | 40 | 97.5% | 96.9% | 0.0% | 0.0% |
| source:ipp-benchmark-v1 | 80 | 98.8% | 98.8% | - | 0.0% |
| source:synthetic | 60 | 96.7% | 95.7% | 0.0% | 0.0% |
| synthetic | 60 | 96.7% | 95.7% | 0.0% | 0.0% |

## Confidence calibration (all docs)

n=126 proposed values, base accuracy 97.6%, ECE **0.0154**, AUROC fused **0.6721** vs model self-confidence 0.7886

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.4-0.5 | 1 | 0.487 | 100.0% |
| 0.7-0.8 | 1 | 0.778 | 100.0% |
| 0.8-0.9 | 4 | 0.855 | 100.0% |
| 0.9-1.0 | 120 | 0.98 | 97.5% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 100.0% | 0.986 |
| 70.0% | 97.7% | 0.98 |
| 80.0% | 97.0% | 0.973 |
| 90.0% | 97.4% | 0.968 |
| 95.0% | 97.5% | 0.925 |
| 100.0% | 97.6% | 0.487 |

## Confidence calibration (held-out test split)

n=71 proposed values, base accuracy 100.0%, ECE **0.0334**, AUROC fused **None** vs model self-confidence None

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.4-0.5 | 1 | 0.487 | 100.0% |
| 0.7-0.8 | 1 | 0.778 | 100.0% |
| 0.8-0.9 | 2 | 0.862 | 100.0% |
| 0.9-1.0 | 67 | 0.98 | 100.0% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 100.0% | 0.986 |
| 70.0% | 100.0% | 0.983 |
| 80.0% | 100.0% | 0.973 |
| 90.0% | 100.0% | 0.955 |
| 95.0% | 100.0% | 0.906 |
| 100.0% | 100.0% | 0.487 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 0 | 10,392 ms | 81,528 ms | 1.3333 | 33.3% | 0.0% | 2,766 | 1,476 | $0.031401 | $0.751 | 7.0 docs/min |

