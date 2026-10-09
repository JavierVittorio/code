"""Compare two eval runs and gate regressions.

    python -m eval.compare outputs/runs/baseline outputs/runs/candidate [--out report.md]

Exit code 1 if the candidate regresses (CI-friendly). Rules:
  FAIL  field accuracy drops and the paired-bootstrap 95% CI of the delta is entirely below 0
  FAIL  hallucination rate rises by more than --max-halluc-increase (default 1 pt)
  FAIL  any single field (n >= 10) loses more than --max-field-drop (default 10 pts)
  FAIL  more failed documents than baseline
  WARN  p95 latency +50%, list-price cost +25%, coverage -5 pts
Runs must share a dataset hash (same docs + same labels); otherwise the comparison is refused.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

GOOD = ("correct", "correct_absent")
# Gate on extraction quality *before* abstention: a threshold change is an operating-point decision (reported
# via coverage/precision warnings), not an extraction regression.
RAW_GOOD = GOOD + ("abstained_lost",)


def _load(run: Path) -> tuple[dict, list[dict]]:
    card = json.loads((run / "scorecard.json").read_text(encoding="utf-8"))
    rows = [json.loads(l) for l in (run / "field_results.jsonl").read_text(encoding="utf-8").splitlines()]
    return card, rows


def paired_bootstrap(a: dict[str, list[int]], b: dict[str, list[int]], n_boot: int = 4000, seed: int = 0):
    """Resample *documents* (fields within a doc are correlated) and return delta mean and 95% CI of accuracy."""
    docs = sorted(set(a) & set(b))
    sa = np.array([sum(a[d]) for d in docs], float)
    sb = np.array([sum(b[d]) for d in docs], float)
    n = np.array([len(a[d]) for d in docs], float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(docs), size=(n_boot, len(docs)))
    deltas = sb[idx].sum(1) / n[idx].sum(1) - sa[idx].sum(1) / n[idx].sum(1)
    point = sb.sum() / n.sum() - sa.sum() / n.sum()
    return float(point), float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))


def compare(base_dir: Path, cand_dir: Path, max_halluc_increase: float = 0.01, max_field_drop: float = 0.10,
            force: bool = False) -> tuple[str, bool]:
    bc, br = _load(base_dir)
    cc, cr = _load(cand_dir)
    bm, cm = bc.get("meta", {}), cc.get("meta", {})
    if bm.get("dataset_hash") != cm.get("dataset_hash") and not force:
        return (f"REFUSED: dataset hash differs ({bm.get('dataset_hash')} vs {cm.get('dataset_hash')}). "
                "Re-run both on the same dataset or pass --force.", False)

    ok_a, ok_b = defaultdict(list), defaultdict(list)
    for r in br:
        ok_a[r["doc_id"]].append(int(r["outcome"] in RAW_GOOD))
    for r in cr:
        ok_b[r["doc_id"]].append(int(r["outcome"] in RAW_GOOD))
    delta, lo, hi = paired_bootstrap(ok_a, ok_b)

    bh, ch = bc["headline"], cc["headline"]
    fails, warns = [], []
    if hi < 0:
        fails.append(f"raw field accuracy dropped {100 * delta:+.1f} pts (95% CI {100 * lo:+.1f} .. {100 * hi:+.1f})")
    dh = (ch["hallucination_rate"] or 0) - (bh["hallucination_rate"] or 0)
    if dh > max_halluc_increase:
        fails.append(f"hallucination rate {100 * (bh['hallucination_rate'] or 0):.1f}% -> {100 * (ch['hallucination_rate'] or 0):.1f}%")
    field_lines = []
    for f in bc["by_field"]:
        a, b = bc["by_field"][f], cc["by_field"].get(f)
        if not b:
            continue
        ka = "raw_accuracy" if "raw_accuracy" in a and "raw_accuracy" in b else "accuracy"
        d = (b[ka] or 0) - (a[ka] or 0)
        mark = ""
        if a["n"] >= 10 and d < -max_field_drop:
            fails.append(f"field `{f}` raw accuracy {100 * a[ka]:.1f}% -> {100 * b[ka]:.1f}%")
            mark = " **FAIL**"
        field_lines.append(f"| {f} | {a['n']} | {_p(a[ka])} | {_p(b[ka])} | {100 * d:+.1f}{mark} | "
                           f"{_p(a['hallucination_rate'])} -> {_p(b['hallucination_rate'])} |")
    if cc["ops"]["failed_docs"] > bc["ops"]["failed_docs"]:
        fails.append(f"failed docs {bc['ops']['failed_docs']} -> {cc['ops']['failed_docs']}")
    bo, co = bc["ops"], cc["ops"]
    if bo.get("latency_ms_p95") and co.get("latency_ms_p95") and co["latency_ms_p95"] > 1.5 * bo["latency_ms_p95"]:
        warns.append(f"p95 latency {bo['latency_ms_p95']:.0f} -> {co['latency_ms_p95']:.0f} ms")
    if bo["list_cost_usd_per_1k_docs"] and co["list_cost_usd_per_1k_docs"] > 1.25 * bo["list_cost_usd_per_1k_docs"]:
        warns.append(f"cost/1k docs ${bo['list_cost_usd_per_1k_docs']} -> ${co['list_cost_usd_per_1k_docs']}")
    if (ch["precision"] or 0) < (bh["precision"] or 0) - 0.01:
        warns.append(f"precision of emitted values {_p(bh['precision'])} -> {_p(ch['precision'])}")
    if (ch["coverage"] or 0) < (bh["coverage"] or 0) - 0.05:
        warns.append(f"coverage {_p(bh['coverage'])} -> {_p(ch['coverage'])}")

    # flips: what exactly changed, so a regression can be debugged and not just detected
    key_a = {(r["doc_id"], r["field"]): r for r in br}
    flips_bad, flips_good = [], []
    for r in cr:
        a = key_a.get((r["doc_id"], r["field"]))
        if not a:
            continue
        was, now = a["outcome"] in GOOD, r["outcome"] in GOOD
        if was and not now:
            flips_bad.append(r)
        elif now and not was:
            flips_good.append(a | {"new_outcome": r["outcome"]})

    passed = not fails
    L = [f"# Regression report: `{bm.get('run_name')}` -> `{cm.get('run_name')}`", "",
         f"**{'PASS' if passed else 'FAIL'}**" + (f" ({len(warns)} warnings)" if warns else ""), "",
         "| | baseline | candidate |", "|---|---|---|",
         *[f"| {k} | `{bm.get(k)}` | `{cm.get(k)}` |" for k in ("model", "prompt_version", "image_profile", "config_fingerprint", "git_sha")],
         "", "| metric | baseline | candidate | delta |", "|---|---|---|---|"]
    for k in ("raw_accuracy", "accuracy", "precision", "hallucination_rate", "coverage", "miss_rate", "wrong_rate", "doc_all_fields_correct"):
        a, b = bh.get(k), ch.get(k)
        L.append(f"| {k} | {_p(a)} | {_p(b)} | {'' if a is None or b is None else f'{100 * (b - a):+.1f} pts'} |")
    L.append(f"| line-item row F1 | {_p(bc['line_items']['row_f1'])} | {_p(cc['line_items']['row_f1'])} | |")
    L.append(f"| p95 latency | {bo.get('latency_ms_p95')} ms | {co.get('latency_ms_p95')} ms | |")
    L.append(f"| input tokens/doc | {bo.get('input_tokens_per_doc')} | {co.get('input_tokens_per_doc')} | |")
    L.append(f"| list $/1k docs | {bo['list_cost_usd_per_1k_docs']} | {co['list_cost_usd_per_1k_docs']} | |")
    L += ["", f"Paired bootstrap over documents (accuracy delta): {100 * delta:+.2f} pts, 95% CI "
              f"[{100 * lo:+.2f}, {100 * hi:+.2f}]", ""]
    if fails:
        L += ["## Failures", *[f"- {f}" for f in fails], ""]
    if warns:
        L += ["## Warnings", *[f"- {w}" for w in warns], ""]
    L += ["## Per field", "", "| field | n | baseline raw acc | candidate raw acc | delta pts | hallucination |", "|---|---|---|---|---|---|",
          *field_lines, "",
          f"## Flips (end-to-end outcome): {len(flips_bad)} newly not-correct, {len(flips_good)} newly right", ""]
    if flips_bad:
        L += ["| doc | field | new outcome | gt | candidate value | conf |", "|---|---|---|---|---|---|"]
        L += [f"| {r['doc_id']} | {r['field']} | {r['outcome']} | {r.get('gt')} | {r.get('raw')} | {r.get('confidence')} |"
              for r in flips_bad[:40]]
    return "\n".join(L) + "\n", passed


def _p(v) -> str:
    return "-" if v is None else f"{100 * v:.1f}%"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--max-halluc-increase", type=float, default=0.01)
    ap.add_argument("--max-field-drop", type=float, default=0.10)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    report, passed = compare(a.baseline, a.candidate, a.max_halluc_increase, a.max_field_drop, a.force)
    if a.out:
        a.out.write_text(report, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(report)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
