"""Versioned prompts. Bump PROMPT_VERSION on any change: it is recorded in every result and run, and
it is part of the cache key (via the message text), so runs stay comparable and caches never lie.
"""
from __future__ import annotations

import json

from .ingest import Page
from .schema import FIELD_SPECS, Kind

PROMPT_VERSION = "v4"

_KIND_FORMAT = {
    Kind.text: "string",
    Kind.ident: "string, exactly as printed",
    Kind.date: "YYYY-MM-DD",
    Kind.money: "plain decimal number, no symbols or thousands separators, e.g. 1234.50",
    Kind.rate: "number in percent, e.g. 11 for 11%",
    Kind.currency: "3-letter ISO code",
    Kind.doctype: "invoice | credit_note",
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
blurry, cut off, handwritten, or when you had to choose between candidates. Do not default to 1.0.
4. Normalize "value" to the requested format; keep "evidence" verbatim.
5. Parties: vendor = the business that ISSUES the invoice and gets paid (letterhead/logo, "From", "Remit to"). \
bill_to = the customer being charged ("Bill to", "Sold to", "Customer", "Invoice to"). ship_to only if a \
distinct delivery block exists ("Ship to", "Deliver to"); otherwise null.
6. invoice_number is ONLY the number labelled as the invoice / tax invoice / credit note / document number \
("Invoice No", "Fatura N.", "Factura", "Fatura-Recibo", "Doc. N.", "Ref. fiscal"). Copy it complete, including a \
series or document-type prefix printed as part of it (e.g. "FT 2019A17/2560", "FR PA9/29", "FAC 4530/735"). \
Purchase order, order, delivery note, quote, account, customer, sale/operation ("Venda", "Operacao", "Num.") and \
"your/our reference" numbers are NOT invoice numbers: if no invoice number is printed, invoice_number is null.
7. Line items: every product/service row across ALL pages, in order, including rows continued on later pages. \
Do NOT include subtotal, tax, discount, shipping-summary or total rows, nor "balance brought forward" rows. \
Use null for a cell that is not printed.
8. Amounts: all money values are positive magnitudes (a credit note's "(120.00)", "-120.00" or "120.00 CR" is 120.00; \
document_type carries the sign). "total" is the invoice grand total including tax; if a withholding/retention is \
deducted after the total, "total" is still the amount before that deduction. "subtotal" is the pre-tax sum of the \
lines as printed (e.g. "Subtotal", "Total excl. VAT", "Total exclusive").
9. Dual currency: if a box such as "TOTAL INVOICE AMOUNT PAYABLE" or "Amount payable in ZAR" states the payable \
amount in a different currency than the lines, then total AND currency come from that payable box.
10. Dates - numeric dates are ambiguous. Decide day/month order from the VENDOR's country (address, phone \
prefix, tax-id format, currency): United States vendors write MM/DD/YYYY; vendors in the UK, Europe, Africa \
(South Africa, Namibia, Zambia...), Asia (Indonesia, India...), Latin America and Australia write DD/MM/YYYY. \
A part greater than 12 settles it. Use the same order for every date on the document.
11. Currency: return the ISO code even when only a symbol is printed, using the vendor's country to resolve \
symbols: "$" from a US vendor = USD, "$" or "N$" from a Namibian vendor = NAD, "R" in South Africa = ZAR, \
"K" in Zambia = ZMW, "£" = GBP, "€" = EUR, "Rp" = IDR. Null only if there is no currency cue at all.
12. vendor_tax_id is the SELLER's tax number (in the seller block: "NIF", "NIPC", "VAT No", "Contribuinte"). \
Never the customer's ("NIF Adquirente", "Cliente", "V/Nc", a number in the customer block), and never \
registration, licence, software-certificate, share-capital or REEE numbers.
13. tax_rate: if one VAT/tax rate applies to all taxed amounts (e.g. a VAT summary line "IVA 23%" or \
"Taxa 23,00"), report it even if it is printed only in the tax summary table. Null if several non-zero rates apply."""


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


LINE_ITEM_COLUMNS = ["description", "quantity", "unit_price", "amount", "page"]


def _compact_skeleton() -> dict:
    """Same information, fewer output tokens: absent fields are omitted (not emitted as null objects) and
    line items are positional rows (keys are not repeated per row; matters for 100+ row invoices)."""
    return {
        "fields": {"<field name>": ["<value>", "<verbatim evidence>", "<page int>", "<confidence 0..1>"]},
        "line_items": [["<description>", "<quantity | null>", "<unit_price | null>", "<amount | null>", "<page>"]],
        "line_items_confidence": "<0..1>",
        "notes": "<optional, short>",
    }


def extraction_messages(pages: list[Page], profile: str, output_format: str = "verbose") -> list[dict]:
    if output_format == "compact":
        shape = ("Return compact JSON in this shape. Include ONLY fields that are printed on the document; omit "
                 "absent fields entirely (omitted = null), but always include document_type and currency. Each field is [value, evidence, page, confidence]; each "
                 "line item is a row [" + ", ".join(LINE_ITEM_COLUMNS) + "]. No whitespace or indentation:\n"
                 + json.dumps(_compact_skeleton()))
    else:
        shape = "Return JSON exactly in this shape (all field keys present):\n" + json.dumps(_skeleton(), indent=1)
    instr = "Extract the invoice below.\n\nField definitions:\n" + _field_guide() + "\n\n" + shape
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
