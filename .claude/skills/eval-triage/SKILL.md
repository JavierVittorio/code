---
name: eval-triage
description: Triage extraction failures from an eval run of this repo. Groups every wrong/missed/hallucinated/abstained field, looks at the actual page image, and assigns each failure a root cause (GT error, prompt, normalizer/metric, validator, model limit) with a concrete fix. Use after `python -m eval.run_eval`, when a scorecard regresses, or when asked "why is field X failing".
argument-hint: "[run dir, default = latest under outputs/runs]"
allowed-tools: Bash(.venv/Scripts/python -m tools.triage:*), Bash(python -m tools.triage:*), Bash(.venv/Scripts/python -m eval.run_eval --rescore:*), Read, Grep, Glob
---

# Eval triage

Goal: turn a scorecard into a short, *actionable* list of root causes. A number going down is not a
finding; "8 of 11 `due_date` misses are US-format dates parsed day-first by the normalizer" is.

## Steps

1. **List failures.** Run `.venv/Scripts/python -m tools.triage $ARGUMENTS` (no argument = latest run).
   Read `scorecard.md` in the same run dir for the headline and by-field tables.

2. **Pick the groups that matter.** Order by count, but always include every `hallucinated` row
   (worst failure kind: a confident value that is not on the page) and every `doc_failed`.

3. **Look at the evidence, not just the numbers.** For each group, inspect 1-3 representative docs:
   - `.venv/Scripts/python -m tools.triage <run> --doc <doc_id>` for the GT-vs-prediction diff, failed checks, and line-item mismatches.
   - `.venv/Scripts/python -m tools.triage <run> --doc <doc_id> --page <n>` renders the page to `outputs/scratch/*.png`; **Read that PNG** and check what is actually printed.

4. **Assign exactly one root cause per failure group:**
   | cause | signature | typical fix |
   |---|---|---|
   | `GT_ERROR` | the page shows the model was right | fix `eval/data/gt/*.json`, record it in `eval/data/GT_CHANGELOG.md` |
   | `METRIC` | values equivalent but scored wrong (format, alias, sign) | fix `eval/matching.py` / `docext/normalize.py` + add a test |
   | `PROMPT` | model systematically misreads a concept (role, which total) | change `docext/prompts.py`, **bump PROMPT_VERSION** |
   | `VALIDATOR` | a check fires on legitimate docs or misses a real inconsistency | change `docext/validate.py` + test |
   | `CONFIDENCE` | wrong value with high confidence, or right value abstained | refit with `python -m tools.calibrate <run>` or add a signal |
   | `MODEL_LIMIT` | page genuinely illegible / handwriting beyond the model | accept; make sure it abstains or is routed to review |

5. **Never edit ground truth to match the model without looking at the page image.** A GT change
   needs the rendered page as evidence and a GT_CHANGELOG entry (doc, field, old -> new, why).

6. **Write the report** to `<run>/triage.md`: one table (cause, field, count, example doc, fix), then
   short notes per cause. End with the 1-3 changes most likely to move the headline metrics, and
   for each say which metric should move and how to verify it (`python -m eval.run_eval --rescore`
   for metric/GT fixes, which costs no API calls; a new run plus `python -m eval.compare` for prompt or model changes).
