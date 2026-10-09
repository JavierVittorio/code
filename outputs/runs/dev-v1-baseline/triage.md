# Triage - dev-v1-baseline

Produced with the `/eval-triage` skill (`.claude/skills/eval-triage`). 38 non-correct fields at first
scoring. Every group below was checked against the rendered page (`tools.triage --doc --page`).
**No ground-truth changes were needed:** every GT label I checked against its page image was right.

| cause | field(s) | count | example doc | fix |
|---|---|---|---|---|
| METRIC | tax_rate, line-item quantity | 1 field + ~40 cells | synth-04-uk-discount | `Decimal.normalize()` produced `2E+1`, which re-parsed as 21. Fixed with `_plain()` in `docext/normalize.py`, plus a regression test |
| METRIC | line-item cells | ~45 cells | synth-06-eu-multipage-scan | Hungarian alignment on description alone cross-matched repeated descriptions. Now uses all labeled cells plus row-order proximity, with a test |
| PROMPT | invoice_date, due_date | 6 | ipp-photo-perspective-severe (`02/08/2025`, ZA vendor, read as Feb 8) | Day/month order must follow vendor country/currency. Say this explicitly in the prompt |
| PROMPT | currency | 5 missed + 1 wrong | ipp-clean-us-net30-terms (`$`, US address, returned null) | "Only if unambiguous" was too strict. Infer from symbol + vendor country; a bare `$` from a Namibian vendor means NAD |
| PROMPT | invoice_number | 1 hallucinated | ipp-hard-missing-invoice-number-1 (delivery note `DN24541` used as invoice no.) | PO, delivery-note, order and reference numbers are not invoice numbers; null if no invoice number is printed |
| PROMPT | total, subtotal, currency, tax | 4 | ipp-currency-dual-usd-zar-1 | Model used the USD line currency, not the ZAR "amount payable" box. Restate the rule with the box name |
| PROMPT | subtotal | 1 missed | ipp-tax-inclusive-total-za | VAT-inclusive layout: subtotal = total minus VAT ("total excl. VAT") |
| MODEL_LIMIT | invoice_number, dates, amounts | ~10 | ipp-photo-motion-blur-severe ("2 August 2025" read as "1 August 2023"; the blur is illegible to a human too, GT confirmed on the legible sibling ipp-photo-crumple-severe, same base invoice) | Severe blur/noise. These **should be abstained**, but confidence was 0.93-0.99 (see below) |
| CONFIDENCE | all | systemic | the photo slice | Model self-confidence is ~1.0 for everything (AUROC 0.51). Grounding was low on most of the misreads (0.27-0.55) but the hand-set prior under-weights it. Fit fusion on the calib split (`tools/calibrate.py`) |

## Notes

- **METRIC fixes come first** because they change what every later number means. Both fixes were
  verified by `--rescore` (no API calls). Field accuracy went 93.7% -> 93.9%; quantity cells 78% -> 95%,
  unit_price 84% -> 95%.
- **Day/month errors are the biggest model-side cluster.** They are near-misses that pass every
  arithmetic check, so no validator catches them. Only the prompt (locale reasoning) or grounding
  against an unambiguous rendering can.
- **Severe photo degradation:** the misreads are mostly unrecoverable for this model. The right
  behaviour is to abstain or flag. Grounding scores separate them reasonably well, which makes this
  a calibration problem, not an extraction one.

## Most likely to move the headline

1. **Prompt v2** (locale-aware dates, currency inference, invoice-number exclusions, payable box,
   tax-inclusive subtotal). Expected: invoice_date/due_date +5-8 pts, currency +8 pts, hallucination
   rate down. Verify with a new run and `python -m eval.compare dev-v1-baseline dev-v2`.
2. **Fit confidence fusion** on the calib split. Expected: AUROC up and abstentions landing on the
   photo-slice misreads. Verify with `python -m tools.calibrate <run>`, which reports test-split
   ECE/AUROC before and after.
3. Optional: the metric fixes are already in. Re-run `--rescore` whenever `eval/matching.py` changes.
