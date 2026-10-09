"""Failure triage helper (backs the `/eval-triage` Claude Code skill, usable by humans too).

    python -m tools.triage outputs/runs/<run>                    # grouped failure listing
    python -m tools.triage outputs/runs/<run> --doc <id> --page 2 # render that page to PNG for inspection
    python -m tools.triage outputs/runs/<run> --doc <id>          # full GT vs prediction diff for one doc

Prints every non-correct (doc, field) grouped by outcome then field, with GT, the model's raw value,
its verbatim evidence, page, fused confidence and the signals that produced it, so each failure can
be assigned a root cause (GT error / prompt / normalizer / validator / model limit / metric).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from eval.dataset import load_dataset

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "outputs" / "scratch"
GOOD = {"correct", "correct_absent"}


def _rows(run: Path) -> list[dict]:
    return [json.loads(l) for l in (run / "field_results.jsonl").read_text(encoding="utf-8").splitlines()]


def _preds(run: Path) -> dict[str, dict]:
    return {p["doc_id"]: p for p in map(json.loads, (run / "predictions.jsonl").read_text(encoding="utf-8").splitlines())}


def listing(run: Path, max_per_group: int) -> None:
    rows = [r for r in _rows(run) if r["outcome"] not in GOOD]
    groups: dict[tuple, list] = defaultdict(list)
    for r in rows:
        groups[(r["outcome"], r["field"])].append(r)
    print(f"{len(rows)} non-correct fields in {run.name}\n")
    for (outcome, field), rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"## {outcome} / {field}  ({len(rs)})")
        for r in rs[:max_per_group]:
            sig = r.get("signals") or {}
            print(f"  - {r['doc_id']}: gt={r.get('gt')!r} raw={r.get('raw')!r} page={r.get('page')} "
                  f"conf={r.get('confidence')} self={sig.get('self_conf')} ground={sig.get('grounding')} "
                  f"chk+{sig.get('checks_passed', 0)}/-{sig.get('checks_failed', 0)}"
                  f"{' reasked' if sig.get('reasked') else ''}{' NEAR' if r.get('near_miss') else ''}")
            if r.get("evidence"):
                print(f"      evidence: {str(r['evidence'])[:140]!r}")
        if len(rs) > max_per_group:
            print(f"  ... {len(rs) - max_per_group} more")
        print()
    preds = _preds(run)
    failed = [p for p in preds.values() if p.get("status") != "ok"]
    if failed:
        print("## failed documents")
        for p in failed:
            print(f"  - {p['doc_id']}: {p.get('error')}")


def doc_diff(run: Path, doc_id: str) -> None:
    gt = {d.doc_id: d for d in load_dataset()}[doc_id]
    p = _preds(run)[doc_id]
    print(f"# {doc_id}  file={gt.path.relative_to(ROOT).as_posix()}  tags={gt.tags}")
    print(f"needs_review={p.get('needs_review')} reasons={p.get('review_reasons')}")
    print("checks:", [(c["name"], c["passed"], c["detail"]) for c in p.get("checks", []) if c["passed"] is not True])
    for r in [r for r in _rows(run) if r["doc_id"] == doc_id]:
        mark = "  " if r["outcome"] in GOOD else "XX"
        print(f"{mark} {r['field']:16} {r['outcome']:16} gt={r.get('gt')!r:32} raw={r.get('raw')!r} conf={r.get('confidence')}")
    if gt.line_items is not None:
        print(f"line items: gt={len(gt.line_items)} pred={len(p.get('line_items', []))}")
        for i, (g, q) in enumerate(zip(gt.line_items, p.get("line_items", []) + [{}] * len(gt.line_items))):
            if str(g.get("amount")) != str(q.get("amount")):
                print(f"   row {i + 1}: gt={g.get('description')!r} {g.get('amount')} | pred={q.get('description')!r} {q.get('amount')}")


def render(doc_id: str, page: int) -> None:
    from docext.ingest import load_pages

    gt = {d.doc_id: d for d in load_dataset()}[doc_id]
    pages = load_pages(gt.path.read_bytes(), gt.path.name, "raw", max_pages=99)
    pg = next(p for p in pages if p.index == page)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    out = SCRATCH / f"{doc_id}-p{page}.png"
    img = pg.image
    if max(img.size) > 1800:
        s = 1800 / max(img.size)
        img = img.resize((int(img.width * s), int(img.height * s)))
    img.save(out)
    print(out)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path, nargs="?")
    ap.add_argument("--doc")
    ap.add_argument("--page", type=int)
    ap.add_argument("--max", type=int, default=8)
    a = ap.parse_args()
    run = a.run or max((ROOT / "outputs/runs").iterdir(), key=lambda p: p.stat().st_mtime)
    if a.doc and a.page:
        render(a.doc, a.page)
    elif a.doc:
        doc_diff(run, a.doc)
    else:
        listing(run, a.max)


if __name__ == "__main__":
    main()
