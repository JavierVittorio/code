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
from typing import Any

from pydantic import ValidationError

from . import confidence, grounding, ocr
from .config import Settings
from .ingest import Page, load_pages
from .llm import LLMClient, LLMError, LLMResponse
from .normalize import parse_currency, parse_date, parse_money, parse_number, parse_rate
from .prompts import PROMPT_VERSION, extraction_messages, reask_messages
from .schema import FIELD_SPECS, Check, ExtractedField, ExtractionResult, Kind, LineItem, RawInvoice, Usage
from .validate import run_checks

log = logging.getLogger(__name__)

_PARSERS = {
    Kind.text: lambda v: str(v).strip() or None,
    Kind.ident: lambda v: str(v).strip() or None,
    Kind.date: parse_date,
    Kind.money: parse_money,
    Kind.rate: parse_rate,
    Kind.currency: parse_currency,
}
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
            unit_price=None if _is_null(r.unit_price) else parse_money(r.unit_price),
            amount=None if _is_null(r.amount) else parse_money(r.amount),
            page=r.page,
        ))
    return items


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
                                "image_profile": self.s.image_profile, "calibration": confidence.COEF_VERSION,
                                "abstain_threshold": self.s.abstain_threshold, "attempts": []}
        try:
            pages = await asyncio.to_thread(load_pages, data, filename, self.s.image_profile, self.s.max_pages)
            meta["pages_sent"] = [p.index for p in pages]
            meta["total_pages"] = pages[0].meta["total_pages"] if pages else 0

            raw_dict, raw = await self._call_and_parse(extraction_messages(pages, self.s.image_profile), usage, meta)
            typed, fmt_err = type_fields(raw)
            items = type_line_items(raw)
            checks = run_checks(typed, items, fmt_err)

            reasked: set[str] = set()
            failed = [c for c in checks if c.passed is False]
            if failed:
                fields = sorted({f for c in failed for f in c.fields if f})
                problems = [c.detail or c.name for c in failed]
                try:
                    fix_dict, fix = await self._call_and_parse(
                        reask_messages(pages, self.s.image_profile, raw_dict, problems, fields), usage, meta, "reask")
                    raw_dict, raw = _merge(raw_dict, fix_dict, fields)
                    typed, fmt_err = type_fields(raw)
                    items = type_line_items(raw)
                    checks = run_checks(typed, items, fmt_err)
                    reasked = set(fields)
                except (LLMError, ValueError, ValidationError) as e:  # keep first-pass result
                    meta["reask_error"] = str(e)[:300]
                    reasked = set(fields)

            texts = await self._page_texts(pages)
            fields_out = self._finalize(raw, typed, fmt_err, checks, reasked, texts)
            li_conf = _line_item_conf(raw, checks, "line_items" in reasked)
            meta["notes"] = raw.notes
            result = ExtractionResult(doc_id=doc_id, fields=fields_out, line_items=items,
                                      line_items_confidence=li_conf, checks=checks, usage=usage, meta=meta)
        except (LLMError, ValueError, ValidationError) as e:
            log.warning("extraction failed for %s: %s", doc_id, e)
            result = ExtractionResult(doc_id=doc_id, status="failed", error=f"{type(e).__name__}: {e}"[:500],
                                      usage=usage, meta=meta)
        except Exception as e:  # noqa: BLE001 - one bad document must never take down a batch
            log.exception("unexpected failure for %s", doc_id)
            result = ExtractionResult(doc_id=doc_id, status="failed", error=f"{type(e).__name__}: {e}"[:500],
                                      usage=usage, meta=meta)
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
        usage.calls += 0 if r.cache_hit else 1
        usage.input_tokens += r.input_tokens
        usage.output_tokens += r.output_tokens
        usage.cost_usd += r.cost_usd
        usage.list_cost_usd += (r.input_tokens * self.s.price_in_per_mtok + r.output_tokens * self.s.price_out_per_mtok) / 1e6
        usage.cache_hit = usage.cache_hit or r.cache_hit
        meta["attempts"].append({"stage": stage, "model": r.model, "latency_ms": round(r.latency_ms, 1),
                                 "in": r.input_tokens, "out": r.output_tokens, "cache_hit": r.cache_hit,
                                 "retries": r.attempts - 1, "finish": r.extra.get("finish_reason")})

    async def _page_texts(self, pages: list[Page]) -> dict[int, str]:
        if not self.grounding_enabled:
            return {}
        return {p.index: await asyncio.to_thread(ocr.page_text, p) for p in pages}

    def _finalize(self, raw: RawInvoice, typed: dict, fmt_err: dict, checks: list[Check], reasked: set[str],
                  texts: dict[int, str]) -> dict[str, ExtractedField]:
        all_text = "\n".join(texts.values())
        out: dict[str, ExtractedField] = {}
        for name in FIELD_SPECS:
            rf = raw.fields.get(name)
            self_conf = _clamp(rf.confidence if rf and rf.confidence is not None else 0.5)
            raw_val = None if rf is None or _is_null(rf.value) else str(rf.value)
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
        if not isinstance(v, dict):  # bare value instead of {value, evidence, ...}
            f[k] = {"value": v}
    if not isinstance(d.get("line_items"), list):
        d["line_items"] = []
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
