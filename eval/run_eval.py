"""End-to-end eval: send every GT document to the extraction API, score, write a run directory.

    python -m eval.run_eval --api http://localhost:8000 --name baseline
    python -m eval.run_eval --local --name exp-raw-images          # in-process, no API (experiments)
    python -m eval.run_eval --rescore outputs/runs/<run>            # re-score saved predictions (metric changes)

Run directory (outputs/runs/<name>/):
  run_meta.json        model, prompt version, config fingerprint, git sha, dataset hash  -> comparability
  predictions.jsonl    raw API responses, one per document                                -> re-scorable
  field_results.jsonl  one row per (doc, field) with outcome, confidence, signals         -> triage input
  scorecard.json/.md   aggregate metrics
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .dataset import GTDoc, dataset_hash, load_dataset
from .metrics import scorecard
from .report import render_markdown

OUT_ROOT = Path(os.environ.get("EVAL_OUT_DIR", Path(__file__).resolve().parents[1] / "outputs" / "runs"))


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL,
                                       cwd=Path(__file__).parent).decode().strip()
    except Exception:  # noqa: BLE001 - not a git checkout (e.g. inside the container)
        return os.environ.get("GIT_SHA", "unknown")


async def _wait_healthy(client: httpx.AsyncClient, api: str, timeout_s: float = 120) -> dict:
    t0 = time.time()
    while True:
        try:
            r = await client.get(f"{api}/health")
            if r.status_code == 200:
                return r.json()
        except httpx.HTTPError:
            pass
        if time.time() - t0 > timeout_s:
            raise SystemExit(f"API at {api} not healthy after {timeout_s}s")
        await asyncio.sleep(2)


async def run_api(docs: list[GTDoc], api: str, concurrency: int) -> tuple[list[dict], dict]:
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=httpx.Timeout(900)) as client:
        health = await _wait_healthy(client, api)

        async def one(d: GTDoc) -> dict:
            async with sem:
                t0 = time.perf_counter()
                try:
                    r = await client.post(f"{api}/extract", files={"file": (d.path.name, d.path.read_bytes())})
                    r.raise_for_status()
                    pred = r.json()
                except httpx.HTTPError as e:  # transport failure is a failed document, not a crashed eval
                    pred = {"doc_id": d.doc_id, "status": "failed", "error": f"http: {e}", "fields": {},
                            "line_items": [], "needs_review": True,
                            "usage": {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0,
                                      "list_cost_usd": 0, "latency_ms": 0, "cache_hit": False}, "meta": {}}
                pred["doc_id"] = d.doc_id
                pred["client_latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
                _progress(d, pred)
                return pred

        preds = await asyncio.gather(*(one(d) for d in docs))
    return list(preds), health


async def run_local(docs: list[GTDoc], concurrency: int) -> tuple[list[dict], dict]:
    from docext.batch import extract_many
    from docext.config import get_settings
    from docext.extract import Extractor
    from docext.prompts import PROMPT_VERSION

    s = get_settings()
    ex = Extractor(s)
    results = await extract_many(ex, [(d.doc_id, d.path.read_bytes(), d.path.name) for d in docs], concurrency)
    preds = [r.model_dump(mode="json") for r in results]
    for d, p in zip(docs, preds):
        _progress(d, p)
    return preds, {"model": s.model, "prompt_version": PROMPT_VERSION, "image_profile": s.image_profile,
                   "config_fingerprint": s.fingerprint(), "mode": "local"}


def _progress(d: GTDoc, p: dict) -> None:
    u = p.get("usage", {})
    print(f"  {p.get('status', '?'):6} {d.doc_id:45} {u.get('latency_ms', 0):>8.0f}ms "
          f"in={u.get('input_tokens', 0):>6} out={u.get('output_tokens', 0):>5}"
          f"{' cache' if u.get('cache_hit') else ''}{' REVIEW' if p.get('needs_review') else ''}",
          file=sys.stderr, flush=True)


def score_and_write(run_dir: Path, docs: list[GTDoc], preds: list[dict], meta: dict) -> dict:
    by_id = {p["doc_id"]: p for p in preds}
    pairs = [(d, by_id[d.doc_id]) for d in docs if d.doc_id in by_id]
    card, rows = scorecard(pairs)
    card["meta"] = meta
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    with (run_dir / "predictions.jsonl").open("w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p, ensure_ascii=False, default=str) + "\n")
    with (run_dir / "field_results.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    (run_dir / "scorecard.json").write_text(json.dumps(card, indent=1, default=str), encoding="utf-8")
    (run_dir / "scorecard.md").write_text(render_markdown(card), encoding="utf-8")
    return card


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default=os.environ.get("EVAL_API_URL", "http://localhost:8000"))
    ap.add_argument("--local", action="store_true", help="run the extractor in-process instead of via HTTP")
    ap.add_argument("--name", default=os.environ.get("EVAL_RUN_NAME"))
    ap.add_argument("--split", default="all", choices=["all", "calib", "test"])
    ap.add_argument("--only", default="", help="comma-separated doc_id substrings to include")
    ap.add_argument("--concurrency", type=int, default=int(os.environ.get("EVAL_CONCURRENCY", "3")))
    ap.add_argument("--rescore", type=Path, help="re-score an existing run dir without calling the model")
    args = ap.parse_args()

    if args.rescore:
        all_docs = {d.doc_id: d for d in load_dataset()}
        preds = [json.loads(l) for l in (args.rescore / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
        docs = [all_docs[p["doc_id"]] for p in preds if p["doc_id"] in all_docs]
        meta = json.loads((args.rescore / "run_meta.json").read_text(encoding="utf-8"))
        meta["dataset_hash"] = dataset_hash(docs)
        meta["rescored_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        card = score_and_write(args.rescore, docs, preds, meta)
        print(render_markdown(card).split("\n## ")[1])
        return

    docs = load_dataset(split=args.split)
    if args.only:
        keys = [k.strip() for k in args.only.split(",") if k.strip()]
        docs = [d for d in docs if any(k in d.doc_id for k in keys)]
    name = args.name or datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"eval '{name}': {len(docs)} docs -> {'local' if args.local else args.api}", file=sys.stderr)
    t0 = time.perf_counter()
    preds, health = asyncio.run(run_local(docs, args.concurrency) if args.local else run_api(docs, args.api, args.concurrency))
    wall = time.perf_counter() - t0
    meta = {"run_name": name, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "git_sha": _git_sha(), "dataset_hash": dataset_hash(docs), "n_docs": len(docs), "split": args.split,
            "doc_filter": args.only or None, "concurrency": args.concurrency, "wall_s": round(wall, 1),
            "docs_per_min": round(60 * len(docs) / wall, 2) if wall else None, **health}
    card = score_and_write(OUT_ROOT / name, docs, preds, meta)
    print(f"\nwrote {OUT_ROOT / name}", file=sys.stderr)
    print(json.dumps(card["headline"], indent=1))


if __name__ == "__main__":
    main()
