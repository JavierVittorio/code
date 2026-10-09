# Scorecard - dev-v2.1-checks

model `google/gemma-4-31b-it` | prompt `v2` | images `optimized` | config `daf01b1ce98b` | git `ef78f95` | dataset `9f2bcacf0589` (53 docs, split=all)

## Headline

| metric | value | meaning |
|---|---|---|
| field accuracy | **95.9%** | labeled fields whose final answer is right (incl. correct 'absent') |
| precision of emitted values | **96.0%** | of values we returned, share correct |
| hallucination rate | **0.0%** | values returned for fields verified NOT on the page |
| coverage | 100.0% | fields not abstained / failed |
| miss rate | 0.5% | said 'absent' but the field is printed |
| wrong-value rate | 4.0% | emitted a value that does not match (near-miss share 18.2%) |
| abstention precision | - | abstentions that prevented an error |
| docs with every field correct | 75.5% | |

## Review routing (production view)

- straight-through (auto-approved) docs: **71.7%**; of those, fully correct: **84.2%**
- docs whose printed numbers don't reconcile (should be flagged): 3, caught: 100.0%

## Failure taxonomy

| outcome | count |
|---|---|
| correct | 528 |
| correct_absent | 50 |
| missed | 3 |
| wrong | 22 |

## By field

| field | n | accuracy | precision | halluc. | missed | wrong | abstain | outcomes |
|---|---|---|---|---|---|---|---|---|
| document_type | 53 | 100.0% | 100.0% | - | 0.0% | 0.0% | 0.0% |  |
| invoice_number | 53 | 92.5% | 94.1% | 0.0% | 1.9% | 5.8% | 0.0% | missed:1, wrong:3 |
| invoice_date | 53 | 88.7% | 88.7% | - | 0.0% | 11.3% | 0.0% | wrong:6 |
| due_date | 47 | 93.6% | 93.0% | 0.0% | 0.0% | 7.0% | 0.0% | wrong:3 |
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
| total | 53 | 94.3% | 94.3% | - | 0.0% | 5.7% | 0.0% | wrong:3 |

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
| freight | 18 | 100.0% | 100.0% | - | 0.0% |
| handwritten | 26 | 96.2% | 96.2% | - | 0.0% |
| hard | 44 | 97.7% | 97.7% | 0.0% | 0.0% |
| image | 243 | 92.2% | 92.2% | 0.0% | 0.0% |
| locale:EU | 60 | 95.0% | 93.5% | 0.0% | 0.0% |
| locale:ID | 60 | 96.7% | 95.9% | 0.0% | 0.0% |
| locale:UK | 40 | 100.0% | 100.0% | 0.0% | 0.0% |
| locale:US | 80 | 100.0% | 100.0% | 0.0% | 0.0% |
| multipage | 125 | 96.0% | 95.6% | 0.0% | 0.0% |
| photo | 72 | 84.7% | 87.1% | - | 0.0% |
| scan | 45 | 95.6% | 95.6% | - | 0.0% |
| scan:heavy | 40 | 90.0% | 87.5% | 0.0% | 0.0% |
| scan:light | 60 | 98.3% | 97.8% | 0.0% | 0.0% |
| ship_to | 120 | 99.2% | 99.1% | 0.0% | 0.0% |
| should_flag | 27 | 96.3% | 96.3% | - | 0.0% |
| source:ipp-benchmark-v1 | 363 | 94.5% | 95.3% | 0.0% | 0.0% |
| source:synthetic | 240 | 97.9% | 97.4% | 0.0% | 0.0% |
| synthetic | 240 | 97.9% | 97.4% | 0.0% | 0.0% |
| table_split | 80 | 96.2% | 95.7% | 0.0% | 0.0% |
| tax | 26 | 100.0% | 100.0% | - | 0.0% |

## Confidence calibration (all docs)

n=550 proposed values, base accuracy 96.0%, ECE **0.0232**, AUROC fused **0.9026** vs model self-confidence 0.5448

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.7-0.8 | 2 | 0.748 | 0.0% |
| 0.8-0.9 | 5 | 0.846 | 40.0% |
| 0.9-1.0 | 543 | 0.985 | 96.9% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 98.9% | 0.984 |
| 70.0% | 99.2% | 0.982 |
| 80.0% | 99.3% | 0.982 |
| 90.0% | 99.2% | 0.975 |
| 95.0% | 97.7% | 0.96 |
| 100.0% | 96.0% | 0.741 |

## Confidence calibration (held-out test split)

n=290 proposed values, base accuracy 95.2%, ECE **0.0318**, AUROC fused **0.9384** vs model self-confidence 0.4845

| conf bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.7-0.8 | 2 | 0.748 | 0.0% |
| 0.8-0.9 | 1 | 0.841 | 0.0% |
| 0.9-1.0 | 287 | 0.986 | 96.2% |

Risk-coverage (answer only the most confident X%):

| coverage | accuracy | conf threshold |
|---|---|---|
| 50.0% | 100.0% | 0.987 |
| 70.0% | 99.5% | 0.982 |
| 80.0% | 99.6% | 0.982 |
| 90.0% | 99.6% | 0.979 |
| 95.0% | 97.1% | 0.964 |
| 100.0% | 95.2% | 0.741 |

## Cost & latency

| docs | failed | p50 latency | p95 latency | LLM calls/doc | re-ask rate | JSON repair rate | in tok/doc | out tok/doc | billed $ | list-price $ / 1k docs | throughput |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | 0 | - ms | - ms | 0.0189 | 35.9% | 13.2% | 5,027 | 2,539 | $0.195275 | $1.3156 | 53.92 docs/min |

_53 docs served from response cache (excluded from latency percentiles)._
