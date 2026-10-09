"""CI: re-score the committed baseline run from its saved predictions and fail if the headline numbers
differ from the committed scorecard. Catches metric/normalizer changes that would silently move reported
results (a metric change must be committed together with re-scored artifacts). No API calls."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

from .dataset import load_dataset
from .run_eval import score_and_write

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    base = ROOT / "outputs" / "runs" / (ROOT / "outputs" / "BASELINE").read_text().strip()
    committed = json.loads((base / "scorecard.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / base.name
        shutil.copytree(base, tmp)
        docs = {d.doc_id: d for d in load_dataset()}
        preds = [json.loads(l) for l in (tmp / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
        card = score_and_write(tmp, [docs[p["doc_id"]] for p in preds], preds, committed["meta"])
    diffs = {k: (committed["headline"].get(k), v) for k, v in card["headline"].items() if committed["headline"].get(k) != v}
    if diffs:
        print("re-scored baseline differs from committed scorecard:", json.dumps(diffs, indent=1))
        sys.exit(1)
    print(f"metric stability OK ({base.name}: accuracy {card['headline']['accuracy']})")


if __name__ == "__main__":
    main()
