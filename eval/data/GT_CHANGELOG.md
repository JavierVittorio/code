# Ground-truth changelog

Every change to `eval/data/gt/*.json` after import is recorded here: doc, field, old -> new, evidence.
A GT edit without an entry here is a bug: it changes the dataset hash and breaks comparability with
earlier runs.

| date | doc | field | old -> new | evidence / reason |
|---|---|---|---|---|
| 2026-10-09 | (all) | - | initial import | `tools/import_ipp.py` (benchmark answer keys, `scored` fields only) + `tools/synth_invoices.py` (exact by construction) |

Audits that led to **no** change (labels confirmed against the rendered page):
- 2026-10-09 triage of dev-v1-baseline: `ipp-photo-perspective-severe` invoice_date (page shows 02/08/2025 from a ZA
  vendor = 2 Aug, GT right), `ipp-photo-motion-blur-severe` invoice_date/total (the blurred page is not reliably
  legible even to a human reviewer; GT 2 August 2025 / £17,943.95 confirmed on `ipp-photo-crumple-severe`, a legible
  degradation of the same base invoice), `ipp-hard-missing-invoice-number-1` (no invoice number printed, only a
  delivery note number; GT null is right).
