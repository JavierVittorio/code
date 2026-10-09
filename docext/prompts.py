"""Versioned prompts. Bump PROMPT_VERSION on any change: it is recorded in every result and run, and
it is part of the cache key (via the message text), so runs stay comparable and caches never lie.
"""
from __future__ import annotations

import json

from .ingest import Page
from .schema import FIELD_SPECS, Kind

PROMPT_VERSION = "v1"

_KIND_FORMAT = {
    Kind.text: "string",
    Kind.ident: "string, exactly as printed",
    Kind.date: "YYYY-MM-DD",
    Kind.money: "plain decimal number, no symbols or thousands separators, e.g. 1234.50",
    Kind.rate: "number in percent, e.g. 11 for 11%",
    Kind.currency: "3-letter ISO code",
}

SYSTEM = """You are a meticulous invoice data-extraction engine. You read scanned or digital invoice pages \
and return ONLY a JSON object. Accuracy matters more than completeness: a wrong value is far worse than null.

Hard rules:
1. Extract only what is printed on the pages. If a field is not present, set "value": null and "evidence": null. \
Never invent, guess, or compute a value that is not printed (e.g. do not derive a due date from payment terms, \
do not compute tax from a rate).
2. For every non-null value give "evidence": the shortest verbatim snippet from the page that contains it \
(copy the characters as printed, including the original number/date format), and "page": the 1-based page number.
3. "confidence" is your probability (0.0-1.0) that the value is exactly correct. Use low values when text is \
blurry, cut off, handwritten, or when you had to choose between candidates.
4. Normalize "value" to the requested format; keep "evidence" verbatim.
5. Parties: vendor = the business that ISSUES the invoice and gets paid (letterhead/logo, "From", "Remit to"). \
bill_to = the customer being charged ("Bill to", "Sold to", "Customer", "Invoice to"). ship_to only if a \
distinct delivery block exists ("Ship to", "Deliver to"); otherwise null.
6. Line items: every product/service row across ALL pages, in order, including rows continued on later pages. \
Do NOT include subtotal, tax, discount, shipping-summary or total rows, nor "balance brought forward" rows. \
Use null for a cell that is not printed.
7. Amounts: "total" is the final amount payable (grand total / amount due). "subtotal" is before tax and discount.
8. Dates: resolve day/month order using the locale cues on the document (currency, address, other dates)."""


def _skeleton() -> dict:
    return {
        "fields": {
            name: {"value": f"<{_KIND_FORMAT[kind]} | null>", "evidence": "<verbatim | null>", "page": "<int | null>",
                   "confidence": "<0..1>"}
            for name, (kind, _) in FIELD_SPECS.items()
        },
        "line_items": [{"description": "<string>", "quantity": "<number | null>", "unit_price": "<number | null>",
                        "amount": "<number | null>", "page": "<int>"}],
        "line_items_confidence": "<0..1, probability the full line-item table is complete and correct>",
        "notes": "<optional: short note on anything ambiguous>",
    }


def _field_guide() -> str:
    return "\n".join(f"- {n}: {desc}" for n, (_, desc) in FIELD_SPECS.items())


def _image_parts(pages: list[Page], profile: str) -> list[dict]:
    parts: list[dict] = []
    for pg in pages:
        mime, b64 = pg.encoded(profile)
        parts.append({"type": "text", "text": f"--- Page {pg.index} of {pg.meta.get('total_pages', len(pages))} ---"})
        parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    return parts


def extraction_messages(pages: list[Page], profile: str) -> list[dict]:
    instr = (
        "Extract the invoice below.\n\nField definitions:\n" + _field_guide()
        + "\n\nReturn JSON exactly in this shape (all field keys present):\n"
        + json.dumps(_skeleton(), indent=1)
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": [{"type": "text", "text": instr}, *_image_parts(pages, profile)]},
    ]


def reask_messages(pages: list[Page], profile: str, previous: dict, problems: list[str], fields: list[str]) -> list[dict]:
    """Targeted second pass: only the fields implicated by failed checks are re-read."""
    sub = {"fields": {k: previous.get("fields", {}).get(k) for k in fields if k != "line_items"}}
    if "line_items" in fields:
        sub["line_items"] = previous.get("line_items", [])
    instr = (
        "You previously extracted these values from the invoice below:\n" + json.dumps(sub, indent=1, default=str)
        + "\n\nAutomatic consistency checks found problems:\n- " + "\n- ".join(problems)
        + "\n\nRe-read the pages carefully and return corrected JSON with the SAME shape, containing only "
        + "these keys. If the document itself is inconsistent (e.g. the printed total really differs), keep the "
        + "printed values and lower confidence. Do not change a value to make the arithmetic work unless the "
        + "page shows that value. Use null when a value is not printed."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": [{"type": "text", "text": instr}, *_image_parts(pages, profile)]},
    ]
