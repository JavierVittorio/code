# docext: invoice extraction you can measure

A VLM-based extraction service for messy, multi-page invoices, and an evaluation harness that shows
**how often it is right, how it fails, and when it knows it is unsure**.

| final config (`final-v3.1`, 53 docs, 603 labeled fields) | |
|---|---|
| raw field accuracy (before abstention) | **95.4%** |
| precision of returned values @ coverage | **97.5% @ 96.0%** (the rest abstained) |
| hallucination rate (value returned for a field verified absent) | **0.0%** (0/50) |
| line items: row F1 / cell accuracy (amount) | 92.9% / 97.0% |
| auto-approved docs that are fully correct | **91.2%** (v1 baseline: 61.9%) |
| inconsistent invoices routed to review | 3/3 |
| confidence AUROC (test split): fused vs model self-report | **0.93 vs 0.56** |
| p50 latency / throughput / billed cost (uncached, 4 concurrent) | 12.6 s / 10.6 docs/min / $0.0026 per doc |

Model: `google/gemma-4-31b-it` via OpenRouter (any OpenAI-compatible endpoint works).

---

## Run it

```bash
cp .env.example .env            # set LLM_API_KEY (or export OPENROUTER_API_KEY)
docker compose up -d            # extraction API on :8000 (healthchecked)
docker compose run --rm eval    # one-shot eval against the API -> ./outputs/runs/<timestamp>/scorecard.md
```

```bash
curl -F file=@eval/data/docs/ipp/scan-fax-severe.png localhost:8000/extract
curl -F files=@a.pdf -F files=@b.png localhost:8000/extract/batch     # concurrent, per-doc isolation
curl localhost:8000/metrics                                           # tokens, $ and latency since start
```

Without Docker: `pip install -r requirements-dev.txt`, `uvicorn api.app:app`, `python -m eval.run_eval`
(`--local` runs in-process). Tests: `pytest` (50 tests, no network).

| command | what it does |
|---|---|
| `python -m eval.run_eval --name X` | full eval (via API), writes `outputs/runs/X/` |
| `python -m eval.run_eval --rescore outputs/runs/X` | re-score saved predictions (metric/GT changes, **no API calls**) |
| `python -m eval.compare runs/A runs/B` | regression report; **exit 1** on regression |
| `python -m tools.triage runs/X [--doc ID [--page N]]` | failures grouped by kind; GT-vs-pred diff; render page |
| `python -m tools.calibrate runs/X [--write]` | fit/choose confidence fusion + abstain threshold on the calib split |
| `python -m tools.import_ipp` / `python -m tools.synth_invoices` | rebuild the dataset |

---

## Dataset (`eval/data/`, 53 documents, 74 pages)

| source | docs | what it covers | label provenance |
|---|---|---|---|
| [Invoice Extraction Benchmark v1](https://huggingface.co/datasets/drew-ipp/invoice-extraction-benchmark) (CC-BY-4.0), stratified subset | 41 | phone photos (blur, perspective, crumple, crop, low light), scans (fax, noise, stamps, punch holes), handwritten invoice books, 2-8 page invoices with carried-forward rows, credit notes (brackets/CR/minus), VAT-inclusive & Sage layouts, dual-currency payable boxes, missing invoice number, deliberately non-reconciling totals | generator answer keys; **only the keys the benchmark marks as scored** are imported |
| synthetic (`tools/synth_invoices.py`) | 12 | the **full schema** (parties incl. ship-to, PO, tax IDs, terms, discount, rate, qty/unit price), US/EU/ID/UK number + date formats, tables split across pages, decoy "previous balance" amounts, **planted absent fields** (hallucination probes), scan degradation | exact by construction, deterministic bytes |

Ground-truth conventions are designed so the scorecard can be trusted:

- **Labeled vs unlabeled.** A key in `fields` is labeled. `null` means *verified not on the document*
  (a hallucination probe). A missing key means *not labeled* and is not scored, so a correct extraction
  is never counted as a hallucination because a label is missing.
- **Every GT change is audited.** `eval/data/GT_CHANGELOG.md` records audits too. All three triage audits
  so far confirmed the labels against the rendered page; no label has been changed.
- **Split:** a hash of `doc_id` puts 23 docs in `calib` (used to choose the confidence operating point)
  and 30 in `test`.
- **Dataset hash:** GT content + document bytes. `compare` refuses to compare runs on different data.
- `MANIFEST.csv` lists source, split, tags, labeled/absent counts and provenance per document.

**Gap I'd close first:** there are no scans of my own yet. The pipeline needs nothing new to add them:
drop the file in `eval/data/docs/own/`, write a GT JSON (the synthetic GTs are a full-schema template),
then re-run.

## Schema

Flat and typed: `document_type, invoice_number, invoice_date, due_date, currency, po_number, payment_terms,
vendor_{name,address,tax_id}, bill_to_{name,address}, ship_to_{name,address}, subtotal, discount,
other_charges, tax_rate, tax_amount, total` plus `line_items[{description, quantity, unit_price, amount, page}]`.

Every field returns `{value, status: extracted|absent|abstained, confidence, page, evidence, raw_value, signals}`.
**absent** = "not on the document"; **abstained** = "probably there, not sure enough", returned as `value: null`
with the raw guess kept for the reviewer. Money is `Decimal` magnitudes (the sign lives in `document_type`),
and dates are ISO. Each document also gets `needs_review` + `review_reasons`.
Party roles are explicit field prefixes rather than nested objects. That keeps the prompt shorter and
the scoring simpler, without losing the vendor/bill-to/ship-to distinction.

---

## Architecture

```
PDF / image ─► ingest (pypdfium2, EXIF, multi-frame TIFF; text layer if born-digital)
           ─► ONE VLM call, all pages, compact JSON with verbatim evidence + page per value
           ─► parse (tolerant: fences, prose, trailing commas, flat shape) ─► 1 repair turn if invalid
           ─► type + normalize (Decimal, ISO dates, ISO currency; evidence-based separator repair)
           ─► deterministic derivations (VAT-inclusive subtotal; day/month order resolved by payment terms)
           ─► checks: Σlines = subtotal, qty×price = amount, subtotal − discount + charges + tax = total,
                      tax rate, date order/range, ISO currency, value present in PDF text layer
           ─► failed check? ─► ONE targeted re-ask of only the implicated fields, with the failure stated
           ─► grounding: each value vs page text (text layer, else local OCR via RapidOCR)
           ─► confidence fusion (self-report, grounding, checks, re-ask) ─► abstain below threshold
           ─► needs_review if a check still fails or a critical field abstained
```

**Why a single call plus verification, not an agent.** An invoice is 1-8 pages, and every field is
visible at once, so a planner/tool loop adds calls and latency without adding information. The hard
part is *trusting* the output, and that is done in deterministic code. It is cheap, testable, and
produces the features the eval needs. The only "agentic" step is the targeted re-ask. It is triggered
by evidence (a failed check), not by the model deciding to look again. It fires on 24 of 53 docs
(45%): long multi-page tables (one row's qty × price ≠ amount), degraded scans and photos, and the
deliberately inconsistent documents. The row check is the most frequent trigger, and tightening it
(per-row discounts, percentage lines) is an obvious next step for latency.

**No hallucination, by construction:**
1. The prompt requires a verbatim `evidence` snippet and page for every value, and allows null.
2. Values are grounded against text the model didn't produce (text layer or OCR).
3. On born-digital PDFs a date, amount or ID absent from the embedded text is a failed check. This
   caught the model reading "2026" as "2006".
4. Derived values are computed in code, never by the model, and are marked `derived:` in the evidence.

## Evaluation design

- **Failures by kind, not just count.** Each labeled `(doc, field)` is classified as `correct`,
  `wrong` (+`near_miss`: digit transposition or day/month swap), `missed`, `hallucinated`,
  `correct_absent`, `abstained_saved` (abstention prevented an error) or `abstained_lost` (abstention cost
  a right answer), or `doc_failed`. These have different fixes and are reported separately, per field
  and per slice (photo, scan, handwritten, multipage, credit, locale, ...).
- **Two accuracies.** *Raw accuracy* scores extraction quality before abstention. *Accuracy* scores the
  shipped answer. The gate uses raw accuracy, because moving the abstain threshold is an operating-point
  decision, not an extraction regression. That decision shows up as coverage and precision warnings.
- **Line items** are aligned by optimal assignment (Hungarian) on description + cell agreement + row order,
  so one dropped row doesn't shift every later row into "wrong". Reported as row P/R/F1 and per-cell accuracy.
- **Confidence** is evaluated as a product feature: ECE, reliability table, AUROC (does confidence rank
  right above wrong?), and a risk-coverage curve on the held-out split.
- **Production view:** straight-through rate, the accuracy of what is auto-approved, and recall on
  documents that should be flagged.
- **Ops in the same scorecard:** p50/p95 latency, calls/doc, re-ask and JSON-repair rates, tokens/doc,
  billed $ (from OpenRouter `usage.cost`) and list-price $/1k docs.
- **Comparable across versions.** Each run stores model, prompt version, config fingerprint, git SHA and
  dataset hash. Predictions are saved, so metric fixes re-score old runs for free, and CI checks that
  re-scoring the committed baseline reproduces its scorecard (`eval/ci_check.py`).

### Catching a regression before it ships

`eval.compare` resamples **documents** (fields within a doc are correlated) for a paired bootstrap CI,
lists every flipped `(doc, field)`, and exits 1 when:
- raw accuracy drops with its CI entirely below 0,
- hallucination rises more than 1 pt,
- any field drops more than 10 pts, or
- more documents fail.

CI (`.github/workflows/ci.yml`) runs the tests, the metric-stability check, and the gate when a
candidate run is committed. All of it works without an API key.

It did its job during development. The first all-changes-at-once "final" run (`final-v3`) **failed the
gate** (−4.1 pts, CI [−7.0, −1.4]). Decomposing it showed three separate causes, each fixed and
re-gated:
- an over-aggressive abstain threshold fitted on a different image configuration,
- two structurally low confidence signals (currency inferred from a symbol; OCR of handwriting),
- a real bug: the model normalizing `Rp 156.484.000` to `156484.000`.

## Results: how the system got here (all runs committed in `outputs/runs/`)

| run | change | raw acc | precision | halluc. | docs fully right | gate |
|---|---|---|---|---|---|---|
| `dev-v1-baseline` | first prompt | 93.9% | 94.9% | 2.0% | 62.3% | - |
| `dev-v2-prompt` | prompt v2 from triage (locale dates, currency, invoice-no exclusions) | 95.0% | 95.1% | **0.0%** | 67.9% | PASS |
| `dev-v2.1-checks` | text-layer check, terms-based day/month, VAT-incl. subtotal | 95.9% | 96.0% | 0.0% | 75.5% | PASS, +0.8 (CI +0.2..+1.6) |
| `opt-compact-output` | **optimization**: compact output | 95.7% | 96.2% | 0.0% | 73.6% | PASS (−0.2, CI −1.2..+1.0) |
| `final-v3` | + full-fidelity images, prompt v3, fitted threshold 0.93 | 95.0% | 98.2% | 0.0% | 56.6% | **FAIL** (see above) |
| `final-v3.1` | + evidence-based separator repair, currency grounding, threshold 0.95 by cost rule | **95.4%** | **97.5%** | **0.0%** | 66.0%* | PASS |

\* Fewer docs are "fully right" end-to-end because an abstained field counts as not right. By design, those
documents go to review: **91.2% of the auto-approved documents are fully correct**, against 61.9% for v1.

Where it still fails (final, raw accuracy by slice): photos 84.7%, handwritten 88.5%, heavy scans 87.5%,
IDR locale 90.0%, against 98-100% on clean, multipage, credit-note and tax-layout slices. The remaining
errors are mostly digit-level misreads on degraded images (`IN0099973` → `IN009973`). Those are the right
targets for abstention, and the confidence score now ranks them (AUROC 0.93).

## Optimization (measured, with one rejected)

| arm | p50 latency | throughput (4 concurrent) | in/out tokens per doc | billed $ (53 docs) | raw acc |
|---|---|---|---|---|---|
| verbose JSON (`dev-v2-prompt`) | 24.0 s | 6.6 docs/min | 4,892 / 2,536 | $0.203 | 95.0% |
| **compact JSON** (`opt-compact-output`) | **6.2 s** | **13.8 docs/min** | 2,693 / 1,398 | **$0.097** | 95.7% |

**Adopted: compact output.** Absent fields are omitted, each field is `[value, evidence, page, conf]`, and
line items are positional rows. Latency here is dominated by *output* tokens, so this was the lever: p50
−74%, throughput ×2.1, cost −52%, JSON-repair rate 13% → 0%, accuracy unchanged within CI. One side
effect showed up in the flips (the model occasionally omitted `currency`). It was fixed in v3 by naming
the always-present fields.

**Rejected: image downscaling.** The 150 DPI grayscale JPEG profile was meant to cut vision tokens.
Measured on 12 hard docs, it saved **no** tokens (Gemma charges about a fixed amount per image) and lost
**6.4 pts** (CI +1.7..+9.9 in favour of full-fidelity images) to digit misreads on scans. It stays in the
code as `IMAGE_PROFILE=optimized` for providers that bill by pixel. It is not the default.

The final config pairs compact output with full-fidelity images (`final-v3`, uncached): p50 12.6 s,
10.6 docs/min, $0.0026 per doc. That is cheaper and faster than v1 (29.7 s, 5.8 docs/min, $0.0037)
while being more accurate. The **response cache** (content-addressed on the exact request) makes re-runs
of unchanged documents free; re-evaluating code-only changes cost about $0.

## Confidence and abstention

The model's own confidence is useless: it reports ~1.0 for everything, with AUROC 0.48-0.56 on held-out
fields. The fused score (logistic over self-confidence, grounding, checks passed/failed, re-asked,
format-ok) reaches **AUROC 0.93**. Almost all of that signal comes from grounding and failed checks,
which are computed in code.

I tried fitting the fusion weights on the calib split, using L2 toward the prior chosen by 5-fold CV.
That fit helped on one run (test AUROC 0.94 → 0.96) and hurt on the next (0.93 → 0.84). With about 15
calib errors it is unstable, so the shipped coefficients are the hand-set prior (`--prior-only`).
**Caveat:** that choice was informed by test-split behaviour across two runs. More labeled errors are
the real fix.

The threshold (0.95) is chosen on calib by an explicit cost rule: a silently wrong value costs five
manual checks. Both numbers live in `docext/calibration.json` and are reported in every result's `meta`.

## Production notes

- **Concurrency.** Asyncio semaphore, per-document isolation (one bad file never fails a batch), and an
  `/extract/batch` endpoint. The batch eval found a real crash: **pdfium is not thread-safe**, and
  concurrent rendering segfaulted the process. Rendering is now serialized behind a lock (with a test);
  LLM calls stay concurrent.
- **Resilience.** Retries with jittered backoff and `Retry-After` on 429/5xx/timeouts. Model fallback that
  retries once, then moves on: the free Gemma pool on OpenRouter was rate-limited upstream throughout
  development, so the paid twin of the same model is the default fallback. JSON-mode negotiation (falls
  back if a provider rejects `response_format`), one repair turn on invalid JSON, and a structured
  `failed` result instead of an exception. Corrupt or empty uploads return a structured failure or 400.
- **Cost visibility.** Billed cost from the provider plus list-price cost per result, `/metrics`, and per-run
  ops in the scorecard. Cache hits are reported as $0.

## Key trade-offs

- **VLM-only extraction, OCR only for verification.** Layout and tables survive better in pixels than
  in OCR text, and OCR is noisy on exactly the documents that matter, so it is a confidence feature,
  never a source of values. The PDF text layer is exact, so it *is* used as a hard check.
- **Code over model for anything checkable** (arithmetic, day/month order from terms, derived subtotal).
  It is deterministic, testable and explainable in `review_reasons`.
- **Precision over coverage.** At a 5:1 error:review cost, abstaining on 4% of fields to lift precision
  from 95.4% to 97.5% is worth it. A different cost ratio gives a different threshold with no code change.
- **Small, honest dataset.** 53 documents is enough to rank changes with paired CIs and too few to
  fit confidence weights reliably. Both statements are visible in the numbers.

## Agentic development

Built with Claude Code (Opus 5.5) as a pair: plan mode for the design, then iterative implementation,
with me reviewing diffs, choosing the dataset and making the judgment calls. The git history follows
those steps.

**Custom extensions in `.claude/`:**

- **`/eval-triage` skill** (`.claude/skills/eval-triage/SKILL.md` + `tools/triage.py`). It groups a run's
  failures by kind and field, renders the offending page, has the agent *look at the image*, and assigns
  each group one root cause (GT error / metric / prompt / validator / confidence / model limit). It is
  bound by one rule: never edit GT without page evidence and a changelog entry. Triage of the first
  baseline (`outputs/runs/dev-v1-baseline/triage.md`) found:
  - two *metric* bugs that were mis-scoring correct answers: `Decimal.normalize()` turned 20 into
    `2E+1`, which re-parsed as 21, and line items with repeated descriptions were cross-matched;
  - the prompt issues behind v2: day/month locale, currency from symbol, a delivery-note number
    taken as the invoice number;
  - the confidence problem.

  It also caught the agent itself. While writing the triage report, Claude first read a severely
  blurred date as "3 August"; the skill's evidence rule made it confirm the label on a legible sibling
  degradation of the same base invoice ("2 August", GT right) before recording anything.
- **`PostToolUse` hook** (`.claude/settings.json` → `tools/hooks/test_on_edit.py`). It runs the test suite
  after every edit to `docext/`, `eval/`, `tests/` or `api/`, and feeds failures back to the agent (exit 2),
  so breaks are fixed before they reach a paid eval run.

## What I'd do with more time

1. **Own scans and more labeled errors.** Add 20-30 real scanned invoices, including multi-page and
   non-English ones, and double-label a sample to measure annotator agreement. More errors would make
   calibration fitting stable.
2. **Hybrid input for born-digital PDFs.** Send the text layer alongside the image. It would remove most
   digit misreads on digital PDFs, and the text-layer check already proves the gap exists.
3. **Per-field-kind confidence features** (e.g. OCR grounding is unreliable on handwriting), and
   isotonic calibration once there is data.
4. **Self-consistency only where it pays.** A second sample on abstained or critical fields, then compare
   the cost against the review it saves.
5. **A cheaper-model router.** Try a small model first and escalate when checks fail. The gate and the
   cost columns already provide what's needed to decide.
6. **Async job API** (submit/poll) and a queue for large batches; OpenTelemetry traces per document.

---

```
docext/   config, schema, ingest, ocr, prompts, llm (client, retries, cache), extract (pipeline),
          normalize, validate, grounding, confidence (+calibration.json), batch
api/      FastAPI app
eval/     dataset, matching, metrics, report, run_eval, compare, ci_check; data/ (docs, gt, manifest, changelog)
tools/    import_ipp, synth_invoices, calibrate, triage, hooks/
outputs/  committed runs: predictions, per-field results, scorecards, compare reports, triage
```
