import json
from pathlib import Path

from eval.compare import compare, paired_bootstrap
from eval.dataset import GTDoc
from eval.matching import compare_value, score_line_items
from eval.metrics import classify_doc, scorecard


def _gt(fields, items=None, cells=("description", "amount"), flag=False, doc_id="d1"):
    return GTDoc(doc_id=doc_id, path=Path("x.pdf"), source="t", fields=fields, line_items=items,
                 line_item_cells=list(cells), should_flag=flag, tags=["t"], pages=1, split="test",
                 raw={"fields": fields})


def _pf(value, status="extracted", conf=0.9, raw=None):
    return {"value": value if status == "extracted" else None, "status": status, "confidence": conf,
            "raw_value": raw if raw is not None else (None if status == "absent" else value),
            "signals": {"self_conf": conf}}


def _pred(fields, items=(), review=False):
    return {"status": "ok", "fields": fields, "line_items": list(items), "needs_review": review,
            "usage": {"calls": 1, "input_tokens": 100, "output_tokens": 50, "cost_usd": 0, "list_cost_usd": 0.001,
                      "latency_ms": 1000, "cache_hit": False}, "meta": {"attempts": [{"stage": "extract"}]}}


def test_compare_value_kinds():
    assert compare_value("total", "1,234.50", 1234.5).correct
    assert compare_value("total", "1234.05", 1234.5).near_miss
    assert compare_value("invoice_date", "2024-05-03", "2024-03-05").detail == "day/month swapped"
    assert compare_value("invoice_number", "INV 0012", "inv-0012").correct
    assert compare_value("vendor_name", "ACME Corp.", "Acme Corp").correct
    assert not compare_value("vendor_name", "Globex", "Acme Corp").correct
    assert compare_value("total", "52.94", 976.81, alts=[52.94]).correct


def test_taxonomy():
    gt = _gt({"total": "10.00", "po_number": None, "due_date": "2024-01-31", "invoice_number": "A1",
              "vendor_name": "Acme", "currency": "USD", "subtotal": "9.00"})
    pred = _pred({
        "total": _pf("10.00"),
        "po_number": _pf("PO-1"),  # GT says not printed -> hallucinated
        "due_date": _pf(None, "absent"),  # printed but missed
        "invoice_number": _pf(None, "abstained", 0.3, raw="A7"),  # abstained on a wrong value -> saved
        "vendor_name": _pf(None, "abstained", 0.4, raw="Acme"),  # abstained on a right value -> lost
        "currency": _pf("EUR"),  # wrong
        # subtotal missing from prediction entirely -> treated as absent -> missed
    })
    out = {r["field"]: r["outcome"] for r in classify_doc(gt, pred)}
    assert out == {"total": "correct", "po_number": "hallucinated", "due_date": "missed",
                   "invoice_number": "abstained_saved", "vendor_name": "abstained_lost", "currency": "wrong",
                   "subtotal": "missed"}


def test_line_items_hungarian_is_order_and_drop_robust():
    gt = [{"description": "Bolts", "amount": 10}, {"description": "Washers", "amount": 5},
          {"description": "Nuts", "amount": 2}]
    pred = [{"description": "Nuts", "amount": "2.00"}, {"description": "Bolts", "amount": "10.00"}]  # reordered, 1 dropped
    s = score_line_items(pred, gt, ["description", "amount"])
    assert (s.n_gt, s.n_pred, s.matched, s.exact_rows) == (3, 2, 2, 2)


def test_scorecard_end_to_end():
    gt = _gt({"total": "10.00", "po_number": None}, items=[{"description": "A", "amount": 10}], flag=True)
    card, rows = scorecard([(gt, _pred({"total": _pf("10.00"), "po_number": _pf(None, "absent")},
                                       items=[{"description": "A", "amount": "10.00"}], review=True))])
    assert card["headline"]["accuracy"] == 1.0 and card["headline"]["hallucination_rate"] == 0.0
    assert card["line_items"]["row_f1"] == 1.0
    assert card["review_routing"]["should_flag_recall"] == 1.0


def test_bootstrap_detects_clear_regression():
    a = {f"d{i}": [1, 1, 1, 1] for i in range(30)}
    b = {f"d{i}": [1, 0, 0, 1] for i in range(30)}
    d, lo, hi = paired_bootstrap(a, b)
    assert d == -0.5 and hi < 0


def _write_run(tmp: Path, name: str, outcomes: list[str], halluc: float):
    d = tmp / name
    d.mkdir()
    rows = [{"doc_id": f"d{i}", "field": "total", "outcome": o, "gt": "1"} for i, o in enumerate(outcomes)]
    (d / "field_results.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    acc = sum(o == "correct" for o in outcomes) / len(outcomes)
    card = {"meta": {"run_name": name, "dataset_hash": "h"},
            "headline": {"accuracy": acc, "precision": acc, "hallucination_rate": halluc, "coverage": 1.0,
                         "miss_rate": 0, "wrong_rate": 1 - acc, "doc_all_fields_correct": acc},
            "by_field": {"total": {"n": len(outcomes), "accuracy": acc, "hallucination_rate": halluc}},
            "line_items": {"row_f1": 1.0},
            "ops": {"failed_docs": 0, "latency_ms_p95": 1000, "list_cost_usd_per_1k_docs": 1.0, "input_tokens_per_doc": 1}}
    (d / "scorecard.json").write_text(json.dumps(card))
    return d


def test_compare_gate(tmp_path):
    base = _write_run(tmp_path, "base", ["correct"] * 40, 0.0)
    same = _write_run(tmp_path, "same", ["correct"] * 40, 0.0)
    worse = _write_run(tmp_path, "worse", ["correct"] * 25 + ["wrong"] * 15, 0.05)
    assert compare(base, same)[1] is True
    report, passed = compare(base, worse)
    assert passed is False and "hallucination rate" in report and "field accuracy dropped" in report


def test_line_items_repeated_descriptions_align_by_cells_and_order():
    gt = [{"description": "Freight", "quantity": q, "unit_price": "10", "amount": str(10 * q)} for q in (1, 2, 3, 4)]
    pred = [dict(r) for r in gt]
    pred.insert(2, {"description": "Freight", "quantity": "9", "unit_price": "1", "amount": "9"})  # spurious row
    s = score_line_items(pred, gt, ["description", "quantity", "unit_price", "amount"])
    assert s.exact_rows == 4 and s.n_pred == 5
