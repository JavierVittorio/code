"""Ground-truth dataset loading.

GT file contract (eval/data/gt/<doc_id>.json):
  fields         : {name: value | null}. A key that is present is *labeled*; null means "verified not on
                   the document" (a hallucination probe). A missing key means *unlabeled* and is not scored.
  line_items     : list of rows or null (null = line items not labeled)
  line_item_cells: which row cells are labeled (e.g. only description + amount for the public set)
  should_flag    : the document's printed numbers do not reconcile; a correct system routes it to review
  tags           : slice labels used to break metrics down (scan, multipage, handwritten, ...)

Split: a deterministic hash of doc_id assigns ~40% of docs to `calib` (used to fit confidence fusion and pick
the abstain threshold) and the rest to `test` (reported). Never tune on `test`.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


@dataclass
class GTDoc:
    doc_id: str
    path: Path
    source: str
    fields: dict
    line_items: list[dict] | None
    line_item_cells: list[str]
    should_flag: bool
    tags: list[str]
    pages: int
    split: str
    raw: dict = field(repr=False, default_factory=dict)


def split_of(doc_id: str) -> str:
    return "calib" if int(hashlib.sha1(doc_id.encode()).hexdigest(), 16) % 10 < 4 else "test"


def load_dataset(data_dir: Path = DATA_DIR, split: str | None = None) -> list[GTDoc]:
    docs = []
    for p in sorted((data_dir / "gt").glob("*.json")):
        g = json.loads(p.read_text(encoding="utf-8"))
        d = GTDoc(doc_id=g["doc_id"], path=data_dir / g["file"], source=g["source"], fields=g["fields"],
                  line_items=g.get("line_items"), line_item_cells=g.get("line_item_cells", ["description", "amount"]),
                  should_flag=bool(g.get("should_flag")), tags=g.get("tags", []), pages=g.get("pages", 1),
                  split=g.get("split") or split_of(g["doc_id"]), raw=g)
        if split in (None, "all", d.split):
            docs.append(d)
    return docs


def dataset_hash(docs: list[GTDoc]) -> str:
    """Hash of GT content + document bytes: two runs are only comparable if this matches."""
    h = hashlib.sha256()
    for d in sorted(docs, key=lambda x: x.doc_id):
        h.update(json.dumps(d.raw, sort_keys=True).encode())
        h.update(hashlib.sha256(d.path.read_bytes()).digest())
    return h.hexdigest()[:12]


def write_manifest(docs: list[GTDoc], out: Path = DATA_DIR / "MANIFEST.csv") -> None:
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["doc_id", "file", "source", "split", "pages", "labeled_fields", "absent_probes", "line_items",
                    "should_flag", "tags", "label_provenance"])
        for d in docs:
            w.writerow([d.doc_id, d.path.relative_to(DATA_DIR).as_posix(), d.source, d.split, d.pages, len(d.fields),
                        sum(v is None for v in d.fields.values()),
                        "" if d.line_items is None else len(d.line_items), d.should_flag, " ".join(d.tags),
                        d.raw.get("label_provenance", "")])


if __name__ == "__main__":
    ds = load_dataset()
    write_manifest(ds)
    from collections import Counter
    print(len(ds), "docs", Counter(d.split for d in ds), Counter(d.source for d in ds))
