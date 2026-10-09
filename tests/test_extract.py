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
