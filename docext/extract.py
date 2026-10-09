"""Extraction pipeline: one VLM call over all pages -> parse -> type -> validate -> (targeted re-ask)
-> ground -> fuse confidence -> abstain.

Why a single call + deterministic verification rather than an agent loop: invoices are 1-5 pages and
every field is visible at once, so a planner adds latency/cost without adding information. The
hard part is *trusting* the output, which is done in code (validators, grounding) that is cheap,
testable and gives the eval clean features. The single re-ask is the only "agentic" step, and it is
triggered by evidence (a failed check), not by the model.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from . import confidence, grounding, ocr
from .config import Settings
from .ingest import Page, load_pages
from .llm import LLMClient, LLMError, LLMResponse
from .normalize import date_readings, parse_currency, parse_date, parse_doctype, parse_money, parse_number, parse_rate
from .prompts import LINE_ITEM_COLUMNS, PROMPT_VERSION, extraction_messages, reask_messages
from .schema import FIELD_SPECS, Check, ExtractedField, ExtractionResult, Kind, LineItem, RawField, RawInvoice, Usage
from .validate import run_checks

log = logging.getLogger(__name__)

_PARSERS = {
    Kind.text: lambda v: str(v).strip() or None,
    Kind.ident: lambda v: str(v).strip() or None,
    Kind.date: parse_date,
    Kind.money: lambda v: None if (m := parse_money(v)) is None else abs(m),  # magnitudes; sign is in document_type
    Kind.rate: parse_rate,
    Kind.currency: parse_currency,
    Kind.doctype: parse_doctype,
}
# Fields whose abstention alone sends a document to human review.
CRITICAL_FIELDS = ("invoice_number", "invoice_date", "vendor_name", "total", "currency")
_NULLISH = {"", "null", "none", "n/a", "na", "-", "—", "not found", "not present", "unknown"}


# ------------------------------------------------------------------------------ parsing
def parse_model_json(text: str) -> dict:
    """Tolerant JSON extraction: code fences, prose around the object, trailing commas."""
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.S)
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in response")
    s = s[start:end + 1]
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return json.loads(re.sub(r",\s*([}\]])", r"\1", s))


def _is_null(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip().lower() in _NULLISH)


def _money_from_evidence(val: Decimal, evidence: str) -> Decimal:
    """The model normalizes '1.234.567' (IDR/EU thousands) to '1234.567' surprisingly often, which parses as
    1234.57. The verbatim evidence is unambiguous: if it has the same digits but parses differently, trust it."""
    ev = parse_money(evidence)
    if ev is None or abs(ev) == val:
        return val
    digits = lambda x: re.sub(r"\D", "", str(x)).lstrip("0").rstrip("0")  # noqa: E731
    return abs(ev) if digits(ev) == digits(val) and abs(ev) > val else val


def type_fields(raw: RawInvoice) -> tuple[dict[str, Any], dict[str, str]]:
    """Raw model values -> typed values. Returns (typed, format_errors)."""
    typed: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for name, (kind, _) in FIELD_SPECS.items():
        rf = raw.fields.get(name)
        if rf is None or _is_null(rf.value):
            typed[name] = None
            continue
        val = _PARSERS[kind](rf.value)
        if kind == Kind.money and val is not None and rf.evidence:
            val = _money_from_evidence(val, rf.evidence)
        if val is None:
            errors[name] = f"could not parse {rf.value!r} as {kind.value}"
        typed[name] = val
    return typed, errors


def type_line_items(raw: RawInvoice) -> list[LineItem]:
    items = []
    for r in raw.line_items:
        if _is_null(r.description) and all(_is_null(x) for x in (r.quantity, r.unit_price, r.amount)):
            continue
        items.append(LineItem(
            description=None if _is_null(r.description) else str(r.description).strip(),
            quantity=None if _is_null(r.quantity) else parse_number(r.quantity),
            unit_price=None if _is_null(r.unit_price) else _abs(parse_money(r.unit_price)),
            amount=None if _is_null(r.amount) else _abs(parse_money(r.amount)),
            page=r.page,
        ))
    return items


def _abs(d):
    return None if d is None else abs(d)


def _analyze(raw: RawInvoice, text_layer: str):
    """Type, derive and check one model response. Pure function of (response, embedded text)."""
    typed, fmt_err = type_fields(raw)
    items = type_line_items(raw)
    derived = derive_fields(typed, items, raw)
    checks = run_checks(typed, items, fmt_err) + text_layer_checks(typed, derived, text_layer)
    return typed, fmt_err, items, derived, checks


def text_layer_checks(typed: dict[str, Any], derived: dict[str, str], text_layer: str) -> list[Check]:
    """Born-digital PDFs carry the exact printed characters. A date/amount/identifier the model reports that is
    nowhere in that text is a misread (e.g. '2006' for a printed '2026'), so it fails a check and is re-asked.
    Not applied to OCR text (too noisy to be a hard check; it only feeds confidence)."""
    if not text_layer:
        return []
    out = []
    for name, (kind, _) in FIELD_SPECS.items():
        v = typed.get(name)
        # computed money (e.g. derived subtotal) is not printed; re-ordered dates still are, so keep checking them
        if v is None or (name in derived and kind == Kind.money) or kind not in (Kind.money, Kind.date, Kind.ident):
            continue
        if kind == Kind.money and v == 0:
            continue  # '0.00' is often implied (blank tax line)
        score = grounding.ground_value(name, v, None, text_layer)
        if score < (0.95 if kind == Kind.ident else 1.0):
            out.append(Check(name=f"text_layer:{name}", passed=False, fields=[name],
                             detail=f"{name} = {v} does not appear in the document's embedded text; re-read it"))
    return out


_TERMS_DAYS = re.compile(r"(?:net\s*(\d{1,3})|(\d{1,3})\s*days?)", re.I)


def _swap(d):
    try:
        return d.replace(day=d.month, month=d.day)
    except ValueError:
        return None


def derive_fields(typed: dict[str, Any], items: list[LineItem], raw: RawInvoice | None = None) -> dict[str, str]:
    """Deterministic, documented derivations (done in code, never by the model). Returns {field: rule}.

    1. VAT-inclusive invoices print 'TOTAL (VAT inclusive)' and 'VAT included' but no pre-tax subtotal. When the
       line amounts sum to the total (prices include VAT), subtotal = total - tax_amount.
    2. Day/month order: if both dates are printed in an ambiguous numeric form and the payment terms say N days,
       exactly one reading makes due - issue == N. Use it (cross-field evidence beats locale guessing).
    """
    derived = {}
    inv, due, terms = typed.get("invoice_date"), typed.get("due_date"), typed.get("payment_terms")
    m = _TERMS_DAYS.search(str(terms or ""))
    if raw is not None and inv and due and m:
        n = int(m.group(1) or m.group(2))
        ev = [str((raw.fields.get(k) or RawField()).evidence or "") for k in ("invoice_date", "due_date")]
        # each printed date is read independently (models are sometimes inconsistent within one document)
        ri, rd = date_readings(ev[0]) or {inv}, date_readings(ev[1]) or {due}
        fits = [(i, d) for i in ri for d in rd if (d - i).days == n]
        if (due - inv).days != n and len(fits) == 1:
            new_inv, new_due = fits[0]
            for k, old_v, new_v in (("invoice_date", inv, new_inv), ("due_date", due, new_due)):
                if new_v != old_v:
                    typed[k] = new_v
                    derived[k] = f"day/month order resolved by payment terms ({n} days)"
    total, tax, sub = typed.get("total"), typed.get("tax_amount"), typed.get("subtotal")
    amounts = [it.amount for it in items if it.amount is not None]
    if sub is None and total is not None and tax and amounts and len(amounts) == len(items) \
            and abs(sum(amounts) - total) <= Decimal("0.02"):
        typed["subtotal"] = total - tax
        derived["subtotal"] = "total - tax_amount (VAT-inclusive line prices)"
    return derived


def review_decision(fields: dict[str, ExtractedField], checks: list[Check]) -> list[str]:
    """Why this document should go to a human (empty list = straight-through)."""
    reasons = [f"check failed: {c.detail or c.name}" for c in checks if c.passed is False]
    reasons += [f"abstained on {k}" for k in CRITICAL_FIELDS if fields.get(k) and fields[k].status == "abstained"]
    return reasons


# ------------------------------------------------------------------------------ pipeline
class Extractor:
    def __init__(self, settings: Settings, client: LLMClient | None = None, grounding_enabled: bool = True):
        self.s = settings
        self.client = client or LLMClient(settings)
        self.grounding_enabled = grounding_enabled

    async def extract(self, data: bytes, filename: str = "", doc_id: str | None = None) -> ExtractionResult:
        doc_id = doc_id or filename or "document"
        t0 = time.perf_counter()
        usage = Usage()
        meta: dict[str, Any] = {"model": self.s.model, "prompt_version": PROMPT_VERSION,
                                "image_profile": self.s.image_profile, "output_format": self.s.output_format,
                                "calibration": confidence.COEF_VERSION,
                                "abstain_threshold": self.s.abstain_threshold, "attempts": []}
        try:
            pages = await asyncio.to_thread(load_pages, data, filename, self.s.image_profile, self.s.max_pages)
            meta["pages_sent"] = [p.index for p in pages]
            meta["total_pages"] = pages[0].meta["total_pages"] if pages else 0

            raw_dict, raw = await self._call_and_parse(
                extraction_messages(pages, self.s.image_profile, self.s.output_format), usage, meta)
            texts = await self._page_texts(pages)
            layer = "\n".join(p.text_layer for p in pages if p.text_layer)
            typed, fmt_err, items, derived, checks = _analyze(raw, layer)

            reasked: set[str] = set()
            failed = [c for c in checks if c.passed is False]
            if failed:
                fields = sorted({f for c in failed for f in c.fields if f})
                problems = [c.detail or c.name for c in failed]
                try:
                    fix_dict, fix = await self._call_and_parse(
                        reask_messages(pages, self.s.image_profile, raw_dict, problems, fields), usage, meta, "reask")
                    raw_dict, raw = _merge(raw_dict, fix_dict, fields)
                    typed, fmt_err, items, derived, checks = _analyze(raw, layer)
                    reasked = set(fields)
                except (LLMError, ValueError, ValidationError) as e:  # keep first-pass result
                    meta["reask_error"] = str(e)[:300]
                    reasked = set(fields)

            fields_out = self._finalize(raw, typed, fmt_err, checks, reasked, texts, derived)
            li_conf = _line_item_conf(raw, checks, "line_items" in reasked)
            meta["notes"] = raw.notes
            reasons = review_decision(fields_out, checks)
            result = ExtractionResult(doc_id=doc_id, fields=fields_out, line_items=items,
                                      line_items_confidence=li_conf, checks=checks, usage=usage, meta=meta,
                                      needs_review=bool(reasons), review_reasons=reasons)
        except (LLMError, ValueError, ValidationError) as e:
            log.warning("extraction failed for %s: %s", doc_id, e)
            result = ExtractionResult(doc_id=doc_id, status="failed", error=f"{type(e).__name__}: {e}"[:500],
                                      usage=usage, meta=meta, needs_review=True, review_reasons=["extraction failed"])
        except Exception as e:  # noqa: BLE001 - one bad document must never take down a batch
            log.exception("unexpected failure for %s", doc_id)
            result = ExtractionResult(doc_id=doc_id, status="failed", error=f"{type(e).__name__}: {e}"[:500],
                                      usage=usage, meta=meta, needs_review=True, review_reasons=["extraction failed"])
        result.usage.latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        return result

    async def _call_and_parse(self, messages: list[dict], usage: Usage, meta: dict,
                              stage: str = "extract") -> tuple[dict, RawInvoice]:
        resp = await self.client.chat(messages)
        self._account(resp, usage, meta, stage)
        try:
            d = parse_model_json(resp.text)
            return d, RawInvoice.model_validate(_coerce_shape(d))
        except (ValueError, ValidationError) as e:
            # one repair turn: show the model its own output and the parser error
            repair = messages + [
                {"role": "assistant", "content": resp.text[:20000]},
                {"role": "user", "content": f"That was not valid JSON for the requested shape ({str(e)[:300]}). "
                                            "Return ONLY the corrected JSON object."},
            ]
            resp2 = await self.client.chat(repair)
            self._account(resp2, usage, meta, stage + "_repair")
            d = parse_model_json(resp2.text)
            return d, RawInvoice.model_validate(_coerce_shape(d))

    def _account(self, r: LLMResponse, usage: Usage, meta: dict, stage: str) -> None:
        # A cache hit is free: no call, no billed tokens. Its original token counts stay visible in meta.attempts.
        if not r.cache_hit:
            usage.calls += 1
            usage.input_tokens += r.input_tokens
            usage.output_tokens += r.output_tokens
            usage.cost_usd += r.cost_usd
            usage.list_cost_usd += (r.input_tokens * self.s.price_in_per_mtok
                                    + r.output_tokens * self.s.price_out_per_mtok) / 1e6
        usage.cache_hit = usage.cache_hit or r.cache_hit
        meta["attempts"].append({"stage": stage, "model": r.model, "latency_ms": round(r.latency_ms, 1),
                                 "in": r.input_tokens, "out": r.output_tokens, "cache_hit": r.cache_hit,
                                 "retries": r.attempts - 1, "finish": r.extra.get("finish_reason")})

    async def _page_texts(self, pages: list[Page]) -> dict[int, str]:
        if not self.grounding_enabled:
            return {}
        return {p.index: await asyncio.to_thread(ocr.page_text, p) for p in pages}

    def _finalize(self, raw: RawInvoice, typed: dict, fmt_err: dict, checks: list[Check], reasked: set[str],
                  texts: dict[int, str], derived: dict[str, str] | None = None) -> dict[str, ExtractedField]:
        all_text = "\n".join(texts.values())
        out: dict[str, ExtractedField] = {}
        for name in FIELD_SPECS:
            rf = raw.fields.get(name)
            self_conf = _clamp(rf.confidence if rf and rf.confidence is not None else 0.5)
            raw_val = None if rf is None or _is_null(rf.value) else str(rf.value)
            if derived and name in derived:  # computed in code from printed values; auditable via evidence
                val = typed[name]
                sig = {"self_conf": 1.0, "grounding": 1.0, "derived": derived[name], "format_ok": True, "reasked": False,
                       "checks_passed": sum(1 for c in checks if c.passed is True and name in c.fields),
                       "checks_failed": sum(1 for c in checks if c.passed is False and name in c.fields)}
                out[name] = ExtractedField(value=val, status="extracted", confidence=round(confidence.fuse(sig), 3),
                                           evidence=f"derived: {derived[name]}", raw_value=str(val), signals=sig)
                continue
            if raw_val is None:
                out[name] = ExtractedField(value=None, status="absent", confidence=round(self_conf, 3))
                continue
            val = typed.get(name)
            page = rf.page if rf.page in texts else None
            text = texts.get(page, "") if page else all_text
            g = grounding.ground_value(name, val, rf.evidence, text) if val is not None and texts else 0.0
            if page and g < 0.9 and val is not None:  # model may cite the wrong page; search whole doc
                g = max(g, grounding.ground_value(name, val, rf.evidence, all_text) * 0.95)
            sig = {
                "self_conf": self_conf,
                "grounding": round(g, 3) if texts else 0.5,  # neutral when grounding disabled
                "checks_passed": sum(1 for c in checks if c.passed is True and name in c.fields),
                "checks_failed": sum(1 for c in checks if c.passed is False and name in c.fields),
                "reasked": name in reasked,
                "format_ok": name not in fmt_err,
            }
            conf = confidence.fuse(sig)
            abstain = val is None or conf < self.s.abstain_threshold
            out[name] = ExtractedField(
                value=None if abstain else val, status="abstained" if abstain else "extracted",
                confidence=round(conf, 3), page=rf.page, evidence=rf.evidence, raw_value=raw_val, signals=sig)
        return out


def _clamp(x: float) -> float:
    try:
        return min(max(float(x), 0.0), 1.0)
    except (TypeError, ValueError):
        return 0.5


def _coerce_shape(d: dict) -> dict:
    """Accept the common deviation where the model returns fields at top level instead of under 'fields'."""
    if "fields" not in d and any(k in d for k in FIELD_SPECS):
        d = {"fields": {k: d[k] for k in FIELD_SPECS if k in d}, **{k: v for k, v in d.items() if k not in FIELD_SPECS}}
    f = d.get("fields") or {}
    for k, v in list(f.items()):
        if isinstance(v, list):  # compact format: [value, evidence, page, confidence]
            f[k] = dict(zip(("value", "evidence", "page", "confidence"), v))
        elif not isinstance(v, dict):  # bare value instead of {value, evidence, ...}
            f[k] = {"value": v}
    if not isinstance(d.get("line_items"), list):
        d["line_items"] = []
    d["line_items"] = [dict(zip(LINE_ITEM_COLUMNS, r)) if isinstance(r, list) else r for r in d["line_items"]]
    return d


def _merge(prev: dict, fix: dict, fields: list[str]) -> tuple[dict, RawInvoice]:
    fix = _coerce_shape(fix)
    merged = json.loads(json.dumps(prev, default=str))
    merged.setdefault("fields", {})
    for k in fields:
        if k in FIELD_SPECS and k in fix.get("fields", {}):
            merged["fields"][k] = fix["fields"][k]
    if "line_items" in fields and fix.get("line_items"):
        merged["line_items"] = fix["line_items"]
        if fix.get("line_items_confidence") is not None:
            merged["line_items_confidence"] = fix["line_items_confidence"]
    return merged, RawInvoice.model_validate(_coerce_shape(merged))


def _line_item_conf(raw: RawInvoice, checks: list[Check], reasked: bool) -> float:
    base = _clamp(raw.line_items_confidence if raw.line_items_confidence is not None else 0.5)
    li = [c for c in checks if "line_items" in c.fields]
    if any(c.passed is False for c in li):
        base *= 0.4
    elif any(c.name == "line_items_sum" and c.passed for c in li):
        base = max(base, 0.9)
    return round(base * (0.9 if reasked else 1.0), 3)
