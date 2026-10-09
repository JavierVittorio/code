"""Scoring: per-field outcome taxonomy -> aggregate metrics -> scorecard dict.

Outcome taxonomy for every *labeled* (doc, field):
  GT has a value:
    correct                 value emitted and matches
    wrong                   value emitted, does not match        (+ near_miss sub-flag)
    missed                  model said "absent"
    abstained_saved         abstained, and the raw value WAS wrong   (abstention prevented an error)
    abstained_lost          abstained, but the raw value was right   (abstention cost a correct answer)
  GT is null (field verified absent on the document):
    correct_absent          model said absent
    hallucinated            value emitted for a field that is not on the page
    abstained_saved         abstained on a value that would have been a hallucination
  doc_failed                extraction failed for the whole document

This is the core of "failures understood by kind": a wrong total, a missed due date and an invented PO
number are different failures with different fixes, and the scorecard reports them separately.
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from typing import Any

import numpy as np

from docext.schema import FIELD_SPECS

from .dataset import GTDoc
from .matching import compare_value, score_line_items

ERROR_OUTCOMES = ("wrong", "hallucinated", "missed")


def classify_doc(gt: GTDoc, pred: dict) -> list[dict]:
    """One row per labeled field: {doc_id, field, outcome, near_miss, confidence, raw_correct, ...}."""
    rows = []
    failed = pred.get("status") != "ok"
    alts = gt.raw.get("alt_values", {})
    for name, gv in gt.fields.items():
        if name not in FIELD_SPECS:
            continue
        row: dict[str, Any] = {"doc_id": gt.doc_id, "field": name, "gt": gv, "split": gt.split}
        if failed:
            rows.append({**row, "outcome": "doc_failed", "pred": None, "confidence": None, "raw_correct": None})
            continue
        pf = pred["fields"].get(name) or {"status": "absent", "value": None, "confidence": 0.0}
        status, raw_val = pf["status"], pf.get("raw_value")
        row.update(pred=pf.get("value"), raw=raw_val, status=status, confidence=pf.get("confidence"),
                   signals=pf.get("signals", {}), evidence=pf.get("evidence"), page=pf.get("page"))
        raw_m = compare_value(name, raw_val, gv, alts.get(name)) if (raw_val is not None and gv is not None) else None
        row["raw_correct"] = (raw_m.correct if raw_m else False) if raw_val is not None else None
        if gv is None:
            outcome = {"absent": "correct_absent", "extracted": "hallucinated", "abstained": "abstained_saved"}[status]
            row["raw_correct"] = False if raw_val is not None else None
        elif status == "absent":
            outcome = "missed"
        elif status == "abstained":
            outcome = "abstained_lost" if row["raw_correct"] else "abstained_saved"
        else:
            m = compare_value(name, pf.get("value"), gv, alts.get(name))
            outcome = "correct" if m.correct else "wrong"
            row["near_miss"] = m.near_miss
            row["detail"] = m.detail
        row["outcome"] = outcome
        rows.append(row)
    return rows


def _rate(num: float, den: float) -> float | None:
    return round(num / den, 4) if den else None


def field_metrics(rows: list[dict]) -> dict:
    c = Counter(r["outcome"] for r in rows)
    present = sum(1 for r in rows if r["gt"] is not None)
    absent = len(rows) - present
    emitted = c["correct"] + c["wrong"] + c["hallucinated"]
    abstained = c["abstained_saved"] + c["abstained_lost"]
    return {
        "n": len(rows),
        # end-to-end: share of labeled fields where the final answer is right (value or correct "absent")
        "accuracy": _rate(c["correct"] + c["correct_absent"], len(rows)),
        # of the values we actually emitted, how many were right (what a downstream system sees)
        "precision": _rate(c["correct"], emitted),
        "coverage": _rate(len(rows) - abstained - c["doc_failed"], len(rows)),
        "hallucination_rate": _rate(c["hallucinated"], absent),
        "miss_rate": _rate(c["missed"], present),
        "wrong_rate": _rate(c["wrong"], present),
        "near_miss_share_of_wrong": _rate(sum(1 for r in rows if r["outcome"] == "wrong" and r.get("near_miss")), c["wrong"]),
        "abstain_rate": _rate(abstained, len(rows)),
        "abstention_precision": _rate(c["abstained_saved"], abstained),  # abstentions that prevented an error
        "outcomes": dict(sorted(c.items())),
    }


def calibration(rows: list[dict], bins: int = 10) -> dict:
    """ECE + reliability table + risk-coverage over fields where a value was proposed (raw_correct known)."""
    pts = [(r["confidence"], bool(r["raw_correct"])) for r in rows
           if r.get("raw_correct") is not None and r.get("confidence") is not None]
    if not pts:
        return {"n": 0}
    conf = np.array([p[0] for p in pts])
    ok = np.array([p[1] for p in pts], dtype=float)
    edges = np.linspace(0, 1, bins + 1)
    table, ece = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf >= lo) & ((conf < hi) | (hi == 1.0))
        if m.sum():
            gap = abs(conf[m].mean() - ok[m].mean())
            ece += m.mean() * gap
            table.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": int(m.sum()), "mean_conf": round(float(conf[m].mean()), 3),
                          "accuracy": round(float(ok[m].mean()), 3)})
    order = np.argsort(-conf)
    acc_at = np.cumsum(ok[order]) / np.arange(1, len(ok) + 1)
    rc = [{"coverage": round(q, 2), "accuracy": round(float(acc_at[max(0, int(q * len(ok)) - 1)]), 4),
           "threshold": round(float(conf[order][max(0, int(q * len(ok)) - 1)]), 3)}
          for q in (0.5, 0.7, 0.8, 0.9, 0.95, 1.0)]
    # AUROC: does confidence rank correct above incorrect? (0.5 = useless)
    pos, neg = conf[ok == 1], conf[ok == 0]
    auroc = float(((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())) \
        if len(pos) and len(neg) else None
    # raw model self-confidence, for comparison against the fused score
    self_c = np.array([r["signals"].get("self_conf", 0.5) for r in rows
                       if r.get("raw_correct") is not None and r.get("confidence") is not None])
    auroc_self = float(((self_c[ok == 1][:, None] > self_c[ok == 0][None, :]).mean()
                        + 0.5 * (self_c[ok == 1][:, None] == self_c[ok == 0][None, :]).mean())) \
        if len(pos) and len(neg) else None
    return {"n": len(pts), "base_accuracy": round(float(ok.mean()), 4), "ece": round(float(ece), 4),
            "auroc_fused": round(auroc, 4) if auroc is not None else None,
            "auroc_self_conf": round(auroc_self, 4) if auroc_self is not None else None,
            "reliability": table, "risk_coverage": rc}


def line_item_metrics(pairs: list[tuple[GTDoc, dict]]) -> dict:
    tot = Counter()
    cells_c, cells_t = Counter(), Counter()
    count_exact = docs = 0
    for gt, pred in pairs:
        if gt.line_items is None:
            continue
        docs += 1
        p_items = [] if pred.get("status") != "ok" else pred.get("line_items", [])
        s = score_line_items(p_items, gt.line_items, gt.line_item_cells)
        tot.update(n_gt=s.n_gt, n_pred=s.n_pred, matched=s.matched, exact=s.exact_rows)
        cells_c.update(s.cells_correct)
        cells_t.update(s.cells_total)
        count_exact += s.n_gt == s.n_pred
    p = _rate(tot["exact"], tot["n_pred"])
    r = _rate(tot["exact"], tot["n_gt"])
    return {"docs": docs, "gt_rows": tot["n_gt"], "pred_rows": tot["n_pred"],
            "row_precision": p, "row_recall": r,
            "row_f1": round(2 * p * r / (p + r), 4) if p and r else 0.0,
            "row_count_exact_rate": _rate(count_exact, docs),
            "cell_accuracy": {c: _rate(cells_c[c], cells_t[c]) for c in cells_t}}


def review_metrics(pairs: list[tuple[GTDoc, dict]], rows_by_doc: dict[str, list[dict]]) -> dict:
    """Production routing view: what happens to docs we auto-approve vs send to a human."""
    stp = stp_ok = flag_tp = flag_fn = should = 0
    for gt, pred in pairs:
        flagged = bool(pred.get("needs_review"))
        fully_ok = all(r["outcome"] in ("correct", "correct_absent") for r in rows_by_doc.get(gt.doc_id, []))
        if not flagged:
            stp += 1
            stp_ok += fully_ok
        if gt.should_flag:
            should += 1
            flag_tp += flagged
            flag_fn += not flagged
    n = len(pairs)
    return {"straight_through_rate": _rate(stp, n),
            "straight_through_doc_accuracy": _rate(stp_ok, stp),  # of auto-approved docs, share fully correct
            "should_flag_docs": should, "should_flag_recall": _rate(flag_tp, should)}


def ops_metrics(preds: list[dict]) -> dict:
    lat = sorted(p["usage"]["latency_ms"] for p in preds if not p["usage"].get("cache_hit"))
    attempts = [a for p in preds for a in p.get("meta", {}).get("attempts", [])]

    def pct(q):
        return round(lat[min(len(lat) - 1, int(q * len(lat)))], 1) if lat else None

    n = len(preds)
    return {
        "documents": n,
        "failed_docs": sum(p.get("status") != "ok" for p in preds),
        "latency_ms_p50": pct(0.5), "latency_ms_p95": pct(0.95),
        "latency_ms_mean": round(statistics.fmean(lat), 1) if lat else None,
        "llm_calls_per_doc": _rate(sum(p["usage"]["calls"] for p in preds), n),
        "reask_rate": _rate(sum(any(a["stage"].startswith("reask") for a in p.get("meta", {}).get("attempts", []))
                                for p in preds), n),
        "json_repair_rate": _rate(sum(any("repair" in a["stage"] for a in p.get("meta", {}).get("attempts", []))
                                      for p in preds), n),
        "http_retries": sum(a.get("retries", 0) for a in attempts),
        "cache_hit_docs": sum(bool(p["usage"].get("cache_hit")) for p in preds),
        "input_tokens_per_doc": _rate(sum(p["usage"]["input_tokens"] for p in preds), n),
        "output_tokens_per_doc": _rate(sum(p["usage"]["output_tokens"] for p in preds), n),
        "cost_usd_total": round(sum(p["usage"]["cost_usd"] for p in preds), 6),
        "list_cost_usd_per_1k_docs": round(1000 * sum(p["usage"]["list_cost_usd"] for p in preds) / max(n, 1), 4),
    }


def scorecard(pairs: list[tuple[GTDoc, dict]]) -> tuple[dict, list[dict]]:
    rows = [r for gt, pred in pairs for r in classify_doc(gt, pred)]
    by_doc = defaultdict(list)
    for r in rows:
        by_doc[r["doc_id"]].append(r)
    by_field = defaultdict(list)
    for r in rows:
        by_field[r["field"]].append(r)
    by_tag = defaultdict(list)
    tags = {gt.doc_id: gt.tags + [f"source:{gt.source}"] for gt, _ in pairs}
    for r in rows:
        for t in tags[r["doc_id"]]:
            if ":" not in t or t.startswith(("source:", "scan:", "locale:")):
                by_tag[t].append(r)
    by_split = defaultdict(list)
    for r in rows:
        by_split[r["split"]].append(r)
    doc_ok = sum(all(r["outcome"] in ("correct", "correct_absent") for r in rs) for rs in by_doc.values())
    card = {
        "headline": {**{k: v for k, v in field_metrics(rows).items() if k != "outcomes"},
                     "doc_all_fields_correct": _rate(doc_ok, len(pairs))},
        "outcomes": field_metrics(rows)["outcomes"],
        "by_split": {s: field_metrics(rs) for s, rs in sorted(by_split.items())},
        "by_field": {f: field_metrics(by_field[f]) for f in FIELD_SPECS if f in by_field},
        "by_tag": {t: field_metrics(rs) for t, rs in sorted(by_tag.items()) if len({r['doc_id'] for r in rs}) >= 2},
        "line_items": line_item_metrics(pairs),
        "review_routing": review_metrics(pairs, by_doc),
        "calibration": calibration(rows),
        "calibration_test_split": calibration([r for r in rows if r["split"] == "test"]),
        "ops": ops_metrics([p for _, p in pairs]),
    }
    return card, rows
