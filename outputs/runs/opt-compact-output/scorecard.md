# Scorecard - opt-compact-output

model `google/gemma-4-31b-it` | prompt `v2` | images `optimized` | config `a546d4253a34` | git `7fc776b` | dataset `9f2bcacf0589` (53 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **95.7%** | labeled fields whose final answer is right (incl. correct 'absent') |
| raw accuracy (before abstention) | 95.7% | extraction quality independent of the abstain threshold |
| precision of emitted values | **96.2%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 100.0% | fields not abstained / failed |
| miss rate | 0.9% | said 'absent' but the field is printed |
| wrong-value rate | 3.8% | emitted a value that does not match (near-miss share 38.1%) |
| abstention precision | - | abstentions that prevented an error |
| docs with every field correct | 73.6% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **66.0%**; of those, fully correct: **80.0%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 100.0%

## Failure taxonomy

| outcome | count |
|---|---|
| correct | 527 |
| correct_absent | 50 |
| missed | 5 |
| wrong | 21 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 53 | 98.1% | 100.0% | - | 1.9% | 0.0% | 0.0% | missed:1 |
| invoice_number | 53 | 92.5% | 94.1% | 0.0% | 1.9% | 5.8% | 0.0% | missed:1, wrong:3 |
| invoice_date | 53 | 88.7% | 88.7% | - | 0.0% | 11.3% | 0.0% | wrong:6 |
| due_date | 47 | 95.7% | 95.3% | 0.0% | 0.0% | 4.7% | 0.0% | wrong:2 |
| currency | 53 | 96.2% | 100.0% | - | 3.8% | 0.0% | 0.0% | missed:2 |
| po_number | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| payment_terms | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| vendor_name | 53 | 98.1% | 98.1% | - | 0.0% | 1.9% | 0.0% | wrong:1 |
| vendor_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| vendor_tax_id | 12 | 83.3% | 77.8% | 0.0% | 0.0% | 22.2% | 0.0% | wrong:2 |
| bill_to_name | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| bill_to_address | 12 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| ship_to_name | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| ship_to_address | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| subtotal | 53 | 96.2% | 96.2% | - | 0.0% | 3.8% | 0.0% | wrong:2 |
| discount | 12 | 91.7% | 75.0% | 0.0% | 0.0% | 25.0% | 0.0% | wrong:1 |
| other_charges | 12 | 100.0% | - | 0.0% | - | - | 0.0% |  |
| tax_rate | 12 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |  |
| tax_amount | 53 | 94.3% | 96.2% | - | 1.9% | 3.8% | 0.0% | missed:1, wrong:2 |
| total | 53 | 96.2% | 96.2% | - | 0.0% | 3.8% | 0.0% | wrong:2 |

## Line items

53 docs, 626 GT rows, 631 predicted. Row P/R/F1 (all labeled cells correct): 93.7% / 94.4% / 94.0%. Row count exact: 92.5%. Cell accuracy: description 96.8%, amount 97.8%, quantity 98.9%, unit_price 98.9%

## By slice

| slice | fields | accuracy | precision | halluc. | abstain |
|---|---|---|---|---|---|
| absent_fields | 200 | 97.5% | 96.8% | 0.0% | 0.0% |
| clean | 44 | 95.5% | 95.5% | - | 0.0% |
| credit | 16 | 93.8% | 100.0% | - | 0.0% |
| currency | 27 | 92.6% | 96.2% | - | 0.0% |
| decoy_amounts | 60 | 100.0% | 100.0% | 0.0% | 0.0% |
| freight | 18 | 100.0% | 100.0% | - | 0.0% |
| handwritten | 26 | 96.2% | 96.2% | - | 0.0% |
| hard | 44 | 97.7% | 97.7% | 0.0% | 0.0% |
| image | 243 | 91.8% | 92.2% | 0.0% | 0.0% |
| locale:EU | 60 | 96.7% | 95.7% | 0.0% | 0.0% |
| locale:ID | 60 | 95.0% | 93.9% | 0.0% | 0.0% |
| locale:UK | 40 | 100.0% | 100.0% | 0.0% | 0.0% |
| locale:US | 80 | 100.0% | 100.0% | 0.0% | 0.0% |
| multipage | 125 | 98.4% | 98.2% | 0.0% | 0.0% |
| photo | 72 | 81.9% | 85.5% | - | 0.0% |
| scan | 45 | 97.8% | 97.8% | - | 0.0% |
| scan:heavy | 40 | 90.0% | 87.5% | 0.0% | 0.0% |
| scan:light | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| ship_to | 120 | 98.3% | 98.1% | 0.0% | 0.0% |
| should_flag | 27 | 96.3% | 96.3% | - | 0.0% |
| source:ipp-benchmark-v1 | 363 | 94.2% | 95.5% | 0.0% | 0.0% |
| source:synthetic | 240 | 97.9% | 97.4% | 0.0% | 0.0% |
| synthetic | 240 | 97.9% | 97.4% | 0.0% | 0.0% |
| table_split | 80 | 97.5% | 97.1% | 0.0% | 0.0% |
| tax | 26 | 100.0% | 100.0% | - | 0.0% |

## Confidence calibration (all docs)

n=548 proposed values, base accuracy 96.2%, ECE **0.01**, AUROC fused **0.9315** vs model self-confidence 0.7293

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.2-0.3 | 2 | 0.278 | 0.0% |
| 0.4-0.5 | 3 | 0.461 | 0.0% |
| 0.7-0.8 | 1 | 0.708 | 0.0% |
| 0.8-0.9 | 21 | 0.84 | 85.7% |
| 0.9-1.0 | 521 | 0.982 | 97.7% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 100.0% | 0.986 |
| 70.0% | 100.0% | 0.985 |
| 80.0% | 99.1% | 0.976 |
| 90.0% | 98.8% | 0.963 |
| 95.0% | 97.7% | 0.911 |
| 100.0% | 96.2% | 0.269 |

## Confidence calibration (held-out test split)

n=289 proposed values, base accuracy 95.5%, ECE **0.0146**, AUROC fused **0.9387** vs model self-confidence 0.7241

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.2-0.3 | 2 | 0.278 | 0.0% |
| 0.7-0.8 | 1 | 0.708 | 0.0% |
| 0.8-0.9 | 13 | 0.837 | 76.9% |
| 0.9-1.0 | 273 | 0.982 | 97.4% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 100.0% | 0.986 |
| 70.0% | 100.0% | 0.984 |
| 80.0% | 99.1% | 0.98 |
| 90.0% | 98.9% | 0.963 |
| 95.0% | 97.5% | 0.895 |
| 100.0% | 95.5% | 0.269 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | 0 | 6,220 ms | 89,976 ms | 1.3774 | 41.5% | 0.0% | 2,693 | 1,398 | $0.097179 | $0.7176 | 13.76 docs/min |

_2 docs served from response cache (excluded from latency percentiles)._
