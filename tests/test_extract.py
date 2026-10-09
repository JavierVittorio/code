"""Pipeline tests with a scripted fake LLM: no network, deterministic."""
import asyncio
import io
import json
from dataclasses import replace

from PIL import Image, ImageDraw

from docext.config import Settings
from docext.extract import Extractor
from docext.llm import LLMError, LLMResponse


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def chat(self, messages, **kw):
        self.calls.append(messages)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return LLMResponse(text=r if isinstance(r, str) else json.dumps(r), model="fake", input_tokens=1000,
                           output_tokens=200, latency_ms=5)


def _png() -> bytes:
    im = Image.new("RGB", (800, 1000), "white")
    d = ImageDraw.Draw(im)
    for i, t in enumerate(["ACME Corp", "Invoice INV-7", "Total 110.00"]):
        d.text((50, 50 + 40 * i), t, fill="black")
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def _f(v, conf=0.95, page=1, ev=None):
    return {"value": v, "evidence": ev or (None if v is None else str(v)), "page": page, "confidence": conf}


GOOD = {"fields": {"invoice_number": _f("INV-7"), "vendor_name": _f("ACME Corp"), "subtotal": _f("100.00"),
                   "tax_amount": _f("10.00"), "total": _f("110.00"), "po_number": _f(None), "currency": _f("USD")},
        "line_items": [{"description": "Widget", "quantity": 2, "unit_price": "50", "amount": "100.00", "page": 1}],
        "line_items_confidence": 0.9}

S = replace(Settings(), cache_enabled=False, abstain_threshold=0.5)


def run(responses, **kw):
    fake = FakeClient(responses)
    ex = Extractor(S, client=fake, grounding_enabled=kw.get("grounding", False))
    return asyncio.run(ex.extract(_png(), "x.png", "doc")), fake


def test_happy_path_single_call_and_typed_output():
    r, fake = run([GOOD])
    assert r.status == "ok" and len(fake.calls) == 1
    assert str(r.fields["total"].value) == "110.00" and r.fields["po_number"].status == "absent"
    assert all(c.passed is not False for c in r.checks) and not r.needs_review
    assert r.usage.input_tokens == 1000 and r.line_items[0].quantity == 2


def test_failed_check_triggers_targeted_reask_and_merges_fix():
    bad = json.loads(json.dumps(GOOD))
    bad["fields"]["total"] = _f("170.00")  # misread
    fix = {"fields": {"total": _f("110.00"), "subtotal": _f("100.00"), "tax_amount": _f("10.00"),
                      "discount": _f(None)}}
    r, fake = run([bad, fix])
    assert len(fake.calls) == 2
    reask_text = fake.calls[1][1]["content"][0]["text"]
    assert "170.00" in reask_text and "total" in reask_text and "invoice_number" not in reask_text
    assert str(r.fields["total"].value) == "110.00" and r.fields["total"].signals["reasked"]
    assert r.fields["invoice_number"].value == "INV-7"  # untouched fields preserved


def test_unfixable_inconsistency_routes_to_review():
    bad = json.loads(json.dumps(GOOD))
    bad["fields"]["total"] = _f("170.00")
    r, _ = run([bad, bad])
    assert r.needs_review and any("total" in x for x in r.review_reasons)


def test_invalid_json_gets_one_repair_turn():
    r, fake = run(["Here you go: {not json", GOOD])
    assert r.status == "ok" and len(fake.calls) == 2
    assert r.meta["attempts"][1]["stage"] == "extract_repair"


def test_llm_failure_is_a_structured_failed_result_not_an_exception():
    r, _ = run([LLMError("all models failed: 429")])
    assert r.status == "failed" and r.needs_review and "429" in r.error


def test_low_confidence_abstains():
    low = json.loads(json.dumps(GOOD))
    low["fields"]["vendor_name"] = _f("ACME Corp", conf=0.05)
    r, _ = run([low], grounding=False)
    f = r.fields["vendor_name"]
    assert f.status == "abstained" and f.value is None and f.raw_value == "ACME Corp"
    assert "abstained on vendor_name" in r.review_reasons


def test_vat_inclusive_subtotal_is_derived_in_code_and_marked():
    inc = json.loads(json.dumps(GOOD))
    inc["fields"]["subtotal"] = _f(None)
    inc["fields"]["total"] = _f("100.00")
    inc["fields"]["tax_amount"] = _f("13.04")
    r, _ = run([inc])
    f = r.fields["subtotal"]
    assert str(f.value) == "86.96" and f.evidence.startswith("derived:") and f.signals["derived"]


def test_compact_output_format_parses_to_same_result():
    compact = {"fields": {"invoice_number": ["INV-7", "INV-7", 1, 0.95], "vendor_name": ["ACME Corp", "ACME Corp", 1, 0.95],
                          "subtotal": ["100.00", "100.00", 1, 0.95], "tax_amount": ["10.00", "10.00", 1, 0.95],
                          "total": ["110.00", "110.00", 1, 0.95], "currency": ["USD", "$", 1, 0.9]},
               "line_items": [["Widget", 2, "50", "100.00", 1]], "line_items_confidence": 0.9}
    r, _ = run([compact])
    assert str(r.fields["total"].value) == "110.00" and r.fields["po_number"].status == "absent"
    assert r.line_items[0].description == "Widget" and r.line_items[0].quantity == 2


def test_payment_terms_resolve_day_month_order():
    from docext.extract import derive_fields, type_fields
    from docext.schema import RawInvoice
    raw = RawInvoice.model_validate({"fields": {
        "invoice_date": {"value": "2026-02-08", "evidence": "02/08/2026"},
        "due_date": {"value": "2026-09-08", "evidence": "09/08/2026"},
        "payment_terms": {"value": "7 days"}}})
    typed, _ = type_fields(raw)
    d = derive_fields(typed, [], raw)
    assert str(typed["invoice_date"]) == "2026-08-02" and str(typed["due_date"]) == "2026-08-09"
    assert "payment terms" in d["invoice_date"]


def test_text_layer_check_flags_value_not_printed():
    from datetime import date
    from decimal import Decimal
    from docext.extract import text_layer_checks
    layer = "Invoice # 021419\nDate: 05/11/2026\nTOTAL $70,774.39"
    typed = {"invoice_date": date(2006, 5, 11), "total": Decimal("70774.39"), "invoice_number": "021419"}
    failed = [c.name for c in text_layer_checks(typed, {}, layer)]
    assert failed == ["text_layer:invoice_date"]
    assert text_layer_checks(typed, {}, "") == []  # scans: no hard check


def test_payment_terms_fix_inconsistent_per_date_readings():
    """Model read one date MM/DD and the other DD/MM (seen on ipp-freight-clearing-na-1)."""
    from docext.extract import derive_fields, type_fields
    from docext.schema import RawInvoice
    raw = RawInvoice.model_validate({"fields": {
        "invoice_date": {"value": "2026-02-08", "evidence": "02/08/2026"},
        "due_date": {"value": "2026-08-09", "evidence": "09/08/2026"},
        "payment_terms": {"value": "7 days"}}})
    typed, _ = type_fields(raw)
    d = derive_fields(typed, [], raw)
    assert str(typed["invoice_date"]) == "2026-08-02" and str(typed["due_date"]) == "2026-08-09"
    assert list(d) == ["invoice_date"]  # only the wrong one is changed
