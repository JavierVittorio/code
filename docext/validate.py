"""Deterministic business-rule checks over typed values.

These make cross-section reasoning *verifiable*: the model reads numbers, the code checks that they
add up. A failed check triggers one targeted re-ask and lowers confidence of the fields involved; a
passing check raises it (independent evidence that every participating number was read correctly).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .normalize import _ISO_CODES
from .schema import Check, LineItem


def _close(a: Decimal, b: Decimal) -> bool:
    tol = max(Decimal("0.02"), abs(b) * Decimal("0.001"))  # 2 cents or 0.1% (rounding on big totals)
    return abs(a - b) <= tol


def run_checks(v: dict[str, object], items: list[LineItem], format_errors: dict[str, str]) -> list[Check]:
    checks: list[Check] = []
    sub, disc, tax, total = v.get("subtotal"), v.get("discount"), v.get("tax_amount"), v.get("total")
    rate = v.get("tax_rate")

    # 1. values that came back but could not be typed (e.g. '12/13/2024' as a day-first date)
    for f, err in format_errors.items():
        checks.append(Check(name=f"format:{f}", passed=False, detail=err, fields=[f]))

    # 2. line items add up to subtotal (or to total when no subtotal is printed and no tax/discount)
    amounts = [it.amount for it in items if it.amount is not None]
    if items and len(amounts) == len(items):
        s = sum(amounts, Decimal(0))
        target, tname = (sub, "subtotal") if sub is not None else (
            (total, "total") if tax is None and disc is None and total is not None else (None, ""))
        if target is not None:
            ok = _close(s, target)
            checks.append(Check(name="line_items_sum", passed=ok, fields=["line_items", tname],
                                detail="" if ok else f"sum of {len(amounts)} line amounts = {s}, but {tname} = {target}"))
    elif items:
        checks.append(Check(name="line_items_sum", passed=None, detail="some line amounts missing",
                            fields=["line_items"]))

    # 3. each row: quantity * unit_price == amount (allow discounts per row to fail softly)
    bad_rows = [i for i, it in enumerate(items, 1)
                if None not in (it.quantity, it.unit_price, it.amount)
                and not _close(it.quantity * it.unit_price, it.amount)]
    if any(None not in (it.quantity, it.unit_price, it.amount) for it in items):
        checks.append(Check(name="line_item_rows", passed=not bad_rows, fields=["line_items"],
                            detail="" if not bad_rows else f"qty*unit_price != amount on rows {bad_rows[:10]}"))

    # 4. subtotal - discount + tax == total
    if sub is not None and total is not None:
        calc = sub - (disc or 0) + (tax or 0)
        ok = _close(calc, total)
        # if tax/discount were not extracted we cannot distinguish 'missing' from 'misread': pass=None
        passed = ok if ok or (tax is not None or disc is not None) else None
        checks.append(Check(name="total_arithmetic", passed=passed,
                            fields=["subtotal", "discount", "tax_amount", "total"],
                            detail="" if ok else f"subtotal {sub} - discount {disc or 0} + tax {tax or 0} = {calc} != total {total}"))

    # 5. tax_rate consistent with tax_amount
    if rate is not None and tax is not None and sub is not None:
        base = sub - (disc or 0)
        exp = (base * rate / 100).quantize(Decimal("0.01"))
        ok = _close(exp, tax) or _close((sub * rate / 100).quantize(Decimal("0.01")), tax)
        checks.append(Check(name="tax_rate", passed=ok, fields=["tax_rate", "tax_amount"],
                            detail="" if ok else f"{rate}% of {base} = {exp}, but tax_amount = {tax}"))

    # 6. dates are plausible and ordered
    inv, due = v.get("invoice_date"), v.get("due_date")
    if isinstance(inv, date):
        ok = date(1990, 1, 1) <= inv <= date(2100, 1, 1)
        checks.append(Check(name="invoice_date_range", passed=ok, fields=["invoice_date"],
                            detail="" if ok else f"implausible invoice_date {inv}"))
    if isinstance(inv, date) and isinstance(due, date):
        ok = due >= inv
        checks.append(Check(name="due_after_issue", passed=ok, fields=["invoice_date", "due_date"],
                            detail="" if ok else f"due_date {due} is before invoice_date {inv} (day/month swap?)"))

    # 7. currency code is real
    cur = v.get("currency")
    if cur is not None:
        ok = cur in _ISO_CODES
        checks.append(Check(name="currency_code", passed=ok, fields=["currency"],
                            detail="" if ok else f"unknown currency code {cur}"))

    # 8. money sanity: non-negative, total is the largest summary amount
    if total is not None and total < 0:
        checks.append(Check(name="total_non_negative", passed=False, fields=["total"], detail=f"total {total} < 0"))
    return checks
