# Scorecard - opt-images-optimized-subset

model `google/gemma-4-31b-it` | prompt `v2` | images `optimized` | config `a546d4253a34` | git `7fc776b` | dataset `bda2917fc309` (12 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **91.4%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 91.4% | extraction quality independent of the abstain threshold |
| precision of emitted values | **90.5%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 100.0% | fields not abstained / failed |
| miss rate | 0.0% | said 'absent' but the field is printed |
| wrong-value rate | 9.5% | emitted a value that does not match (near-miss share 50.0%) |
| abstention precision | - | abstentions that prevented an error |
| docs with every field correct | 66.7% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **75.0%**; of those, fully correct: **77.8%**
- docs whose printed numbers don't reconcile (should be flagged): 0, caught: -

## Failure taxonomy

| outcome | count |
|---|---|
| correct | 114 |
| correct_absent | 14 |
| wrong | 12 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_number | 12 | 91.7% | 91.7% | - | 0.0% | 8.3% | 0.0% | wrong:1 |
| invoice_date | 12 | 83.3% | 83.3% | - | 0.0% | 16.7% | 0.0% | wrong:2 |
| due_date | 11 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| currency | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| po_number | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_address | 3 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_tax_id | 3 | 33.3% | 33.3% | - | 0.0% | 66.7% | 0.0% | wrong:2 |
| bill_to_name | 3 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| bill_to_address | 3 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 3 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 12 | 91.7% | 91.7% | - | 0.0% | 8.3% | 0.0% | wrong:1 |
| discount | 3 | 66.7% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | wrong:1 |
| other_charges | 3 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 3 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| tax_amount | 12 | 83.3% | 83.3% | - | 0.0% | 16.7% | 0.0% | wrong:2 |
| total | 12 | 75.0% | 75.0% | - | 0.0% | 25.0% | 0.0% | wrong:3 |

## Line items

12 docs, 120 GT rows, 124 predicted. Row P/R/F1 (all labeled cells correct): 71.0% / 73.3% / 72.1%. Row count exact: 75.0%. Cell accuracy: description 86.7%, amount 87.5%, quantity 92.6%, unit_price 79.6%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 60 | 83.3% | 78.3% | 0.0% | 0.0% |
| image | 105 | 88.6% | 86.8% | 0.0% | 0.0% |
| locale:ID | 40 | 82.5% | 77.4% | 0.0% | 0.0% |
| multipage | 29 | 89.7% | 87.5% | 0.0% | 0.0% |
| photo | 18 | 88.9% | 88.9% | - | 0.0% |
| scan | 18 | 100.0% | 100.0% | - | 0.0% |
| scan:heavy | 40 | 85.0% | 81.2% | 0.0% | 0.0% |
| source:ipp-benchmark-v1 | 80 | 97.5% | 97.5% | - | 0.0% |
| source:synthetic | 60 | 83.3% | 78.3% | 0.0% | 0.0% |
| synthetic | 60 | 83.3% | 78.3% | 0.0% | 0.0% |

## Confidence calibration (all docs)

n=126 proposed values, base accuracy 90.5%, ECE **0.0627**, AUROC fused **0.924** vs model self-confidence 0.5746

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.1-0.2 | 1 | 0.134 | 0.0% |
| 0.6-0.7 | 4 | 0.67 | 0.0% |
| 0.8-0.9 | 4 | 0.849 | 100.0% |
| 0.9-1.0 | 117 | 0.978 | 94.0% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 100.0% | 0.986 |
| 70.0% | 98.9% | 0.976 |
| 80.0% | 98.0% | 0.973 |
| 90.0% | 95.6% | 0.926 |
| 95.0% | 94.1% | 0.865 |
| 100.0% | 90.5% | 0.134 |

## Confidence calibration (held-out test split)

n=71 proposed values, base accuracy 95.8%, ECE **0.0229**, AUROC fused **0.9608** vs model self-confidence 0.4338

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.8-0.9 | 1 | 0.865 | 100.0% |
| 0.9-1.0 | 70 | 0.978 | 95.7% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 100.0% | 0.986 |
| 70.0% | 100.0% | 0.984 |
| 80.0% | 100.0% | 0.976 |
| 90.0% | 100.0% | 0.955 |
| 95.0% | 98.5% | 0.933 |
| 100.0% | 95.8% | 0.865 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 0 | 9,044 ms | 85,434 ms | 1.3333 | 33.3% | 0.0% | 2,727 | 1,461 | $0.020624 | $0.742 | 8.34 docs/min |

