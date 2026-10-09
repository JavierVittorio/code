"""Grounding: is the extracted value actually on the page?

Independent of the VLM, we read the page text (PDF text layer, else local OCR) and score each value
in [0, 1]. A value the model "saw" but OCR cannot find anywhere is the classic hallucination
signature. OCR is noisy on bad scans, so this is a *feature* for confidence, never a hard filter.
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from rapidfuzz import fuzz

from .normalize import date_readings, norm_ident, norm_text, parse_money
from .schema import FIELD_SPECS, Kind

_CURRENCY_SYMBOLS = {
    "USD": ("$", "US$"), "NAD": ("N$", "$"), "ZAR": ("R ", "R\u00a0", "ZAR"), "ZMW": ("K ", "ZMW"), "GBP": ("£",),
    "EUR": ("€",), "IDR": ("Rp",), "INR": ("₹", "Rs"), "JPY": ("¥",), "AUD": ("A$", "$"), "CAD": ("C$", "$"),
    "SGD": ("S$", "$"), "MYR": ("RM",), "PHP": ("₱",), "THB": ("฿",), "KRW": ("₩",),
}
_NUM_RE = re.compile(r"[-(]?\d[\d.,' ]*\d|\d")


def _numbers(text: str) -> set[Decimal]:
    out = set()
    for m in _NUM_RE.findall(text):
        for cand in {m, m.replace(" ", ""), m.replace("'", "")}:
            v = parse_money(cand)
            if v is not None:
                out.add(abs(v))
    return out


def _date_strings(d: date) -> list[str]:
    mon, mon_s = d.strftime("%B"), d.strftime("%b")
    return [d.isoformat(), f"{d.day:02d}/{d.month:02d}/{d.year}", f"{d.month:02d}/{d.day:02d}/{d.year}",
            f"{d.day}/{d.month}/{d.year}", f"{d.month}/{d.day}/{d.year}", f"{d.day:02d}.{d.month:02d}.{d.year}",
            f"{d.day:02d}-{d.month:02d}-{d.year}", f"{d.day} {mon} {d.year}", f"{mon} {d.day}, {d.year}",
            f"{d.day} {mon_s} {d.year}", f"{mon_s} {d.day}, {d.year}", f"{d.day:02d}/{d.month:02d}/{d.year % 100:02d}",
            f"{d.day:02d}-{mon_s}-{d.year}", f"{d.day:02d}-{mon_s}-{d.year % 100:02d}"]


def ground_value(name: str, value: object, evidence: str | None, text: str) -> float:
    """Return a grounding score in [0,1] for one typed value against page text."""
    if value is None or not text:
        return 0.0
    kind = FIELD_SPECS[name][0]
    hay = norm_text(text)

    if kind in (Kind.money, Kind.rate):
        target = abs(Decimal(value))
        if target in _numbers(text):
            return 1.0
        # evidence present on the page and the evidence itself parses to the value
        if evidence and parse_money(evidence) is not None and abs(parse_money(evidence)) == target:
            return 0.6 * fuzz.partial_ratio(norm_text(evidence), hay) / 100
        return 0.0
    if kind == Kind.date:
        # exact rendering on the page -> fully grounded; fuzzy matches are capped (a 1-char year error is a
        # different date, e.g. '05/11/2006' vs printed '05/11/2026' is 90% similar)
        if any(f" {norm_text(c)} " in f" {hay} " for c in _date_strings(value)):
            return 1.0
        candidates = _date_strings(value) + ([evidence] if evidence else [])
        best = 0.6 * max(fuzz.partial_ratio(norm_text(c), hay) for c in candidates) / 100
        readings = date_readings(evidence) if evidence else set()
        if readings and value not in readings:
            best *= 0.5  # evidence cannot mean this date under any day/month order -> suspicious
        return best
    if kind == Kind.ident:
        v = norm_ident(value)
        if v and v in norm_ident(text):
            return 1.0
        return fuzz.partial_ratio(v, norm_ident(text)) / 100 * 0.9
    if kind == Kind.doctype:
        is_credit = bool(re.search(r"credit|cr[eé]dito|gutschrift", text, re.I))
        return 1.0 if (value == "credit_note") == is_credit else 0.2
    if kind == Kind.currency:
        # Currency is often printed only as a symbol and resolved from the vendor country (prompt rule 11),
        # so a consistent symbol is full evidence; no symbol and no code is genuinely weak evidence.
        if str(value) in text.upper():
            return 1.0
        syms = _CURRENCY_SYMBOLS.get(str(value), ())
        return 1.0 if any(sym in text for sym in syms) else 0.3
    # free text: names/addresses. token_set handles reordering and OCR line breaks.
    v = norm_text(value)
    if not v:
        return 0.0
    return max(fuzz.partial_ratio(v, hay), fuzz.token_set_ratio(v, hay) if len(v) > 20 else 0) / 100
