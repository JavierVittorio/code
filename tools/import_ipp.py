"""Import a stratified subset of the Invoice Extraction Benchmark v1 (CC-BY-4.0, drew-ipp on Hugging Face).

    python -m tools.import_ipp            # downloads docs listed in tools/ipp_subset.txt, writes GT

Mapping rules (benchmark key -> our GT):
  * Only keys in the benchmark's `scored` list become GT. Others are *unlabeled* (key omitted), never
    "absent" - the eval must not count a correct extraction as a hallucination because a label is missing.
  * `tax` -> tax_amount, `lines` -> line_items (description + amount; alt_amounts kept as alternatives).
  * `should_flag` -> should_flag (document should be routed to review: printed numbers don't reconcile).
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://huggingface.co/datasets/drew-ipp/invoice-extraction-benchmark/resolve/main/corpus/v1/"
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "eval/data/docs/ipp"
GT = ROOT / "eval/data/gt"
FIELD_MAP = {"vendor_name": "vendor_name", "invoice_number": "invoice_number", "invoice_date": "invoice_date",
             "due_date": "due_date", "currency": "currency", "subtotal": "subtotal", "tax": "tax_amount",
             "total": "total", "document_type": "document_type"}


def tags_for(r: dict) -> list[str]:
    t = [r["category"], f"difficulty:{r['difficulty']}"]
    if r["pages"] > 1:
        t.append("multipage")
    if r["render"] == "image":
        t.append("image")
    t += [f"degradation:{d['kind']}" for d in r.get("degradations") or []]
    if r["expected"].get("should_flag"):
        t.append("should_flag")
    return list(dict.fromkeys(t))


def main() -> None:
    ids = [l.strip() for l in (ROOT / "tools/ipp_subset.txt").read_text().splitlines() if l.strip()]
    with urllib.request.urlopen(BASE + "metadata.jsonl") as f:
        rows = {r["doc_id"]: r for r in map(json.loads, f.read().decode().splitlines())}
    DOCS.mkdir(parents=True, exist_ok=True)
    GT.mkdir(parents=True, exist_ok=True)
    for doc_id in ids:
        r = rows[doc_id]
        e = r["expected"]
        fname = Path(r["file_name"]).name
        dest = DOCS / fname
        if not dest.exists():
            urllib.request.urlretrieve(BASE + r["file_name"], dest)
        scored = set(e["scored"])
        fields = {ours: e[theirs] for theirs, ours in FIELD_MAP.items() if theirs in scored}
        gt = {
            "doc_id": f"ipp-{doc_id}",
            "file": f"docs/ipp/{fname}",
            "source": "ipp-benchmark-v1",
            "license": "CC-BY-4.0 (drew-ipp/invoice-extraction-benchmark)",
            "label_provenance": "benchmark answer key (generator ground truth)",
            "pages": r["pages"],
            "tags": tags_for(r),
            "description": r["description"],
            "fields": fields,
            "line_items": [{"description": li["description"], "amount": li["amount"],
                            **({"alt_amounts": li["alt_amounts"]} if li.get("alt_amounts") else {})}
                           for li in e["lines"]] if "line_items" in scored else None,
            "line_item_cells": ["description", "amount"],
            "should_flag": bool(e.get("should_flag")),
            "notes": e.get("notes", ""),
        }
        (GT / f"{gt['doc_id']}.json").write_text(json.dumps(gt, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"ok {gt['doc_id']}", file=sys.stderr)


if __name__ == "__main__":
    main()
