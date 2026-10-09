from datetime import date
from decimal import Decimal as D

import pytest

from docext.extract import _coerce_shape, parse_model_json, type_fields, type_line_items
from docext.grounding import ground_value
from docext.normalize import norm_ident, norm_text, parse_currency, parse_date, parse_money, parse_rate
from docext.schema import LineItem, RawInvoice
from docext.validate import run_checks


@pytest.mark.parametrize("s,exp", [
    ("$1,234.56", D("1234.56")), ("1.234,56 €", D("1234.56")), ("1 234,56", D("1234.56")),
    ("(12.00)", D("-12.00")), ("Rp 1.500.000", D("1500000.00")), ("12,5", D("12.50")),
    ("1,234", D("1234.00")), (99.9, D("99.90")), ("abc", None), ("", None), ("0.500", D("0.50")),
])
def test_parse_money(s, exp):
    assert parse_money(s) == exp


@pytest.mark.parametrize("s,exp", [
    ("2024-03-05", date(2024, 3, 5)), ("05/03/2024", date(2024, 3, 5)), ("March 5th, 2024", date(2024, 3, 5)),
    ("5 Mar 2024", date(2024, 3, 5)), ("05-Mar-24", date(2024, 3, 5)), ("garbage", None),
])
def test_parse_date(s, exp):
    assert parse_date(s) == exp


def test_misc_normalizers():
    assert parse_rate("11%") == D("11") and parse_rate(0.1) == D("10")
    assert parse_currency("€") == "EUR" and parse_currency("usd") == "USD" and parse_currency("dollars") is None
    assert norm_ident("INV-00 12") == norm_ident("inv0012")
    assert norm_text("  Café,  Ltd. ") == "cafe ltd"


def test_parse_model_json_tolerates_fences_prose_and_trailing_commas():
    txt = 'Sure! ```json\n{"fields": {"total": {"value": "10.00",},}, "line_items": [],}\n```'
    assert parse_model_json(txt)["fields"]["total"]["value"] == "10.00"
    with pytest.raises(ValueError):
        parse_model_json("I cannot read this document.")


def test_coerce_shape_handles_flat_and_bare_values():
    raw = RawInvoice.model_validate(_coerce_shape({"total": "5.00", "invoice_number": {"value": "A1"}}))
    assert raw.fields["total"].value == "5.00" and raw.fields["invoice_number"].value == "A1"


def _typed(**kw):
    raw = RawInvoice.model_validate({"fields": {k: {"value": v} for k, v in kw.items()}})
    return type_fields(raw)


def test_type_fields_nullish_and_format_errors():
    typed, err = _typed(total="N/A", invoice_date="31/31/2024", subtotal="1,000.00")
    assert typed["total"] is None and "total" not in err
    assert "invoice_date" in err and typed["subtotal"] == D("1000.00")


def test_checks_pass_on_consistent_invoice():
    typed, err = _typed(subtotal="100", tax_amount="10", tax_rate="10", total="110", invoice_date="2024-01-01",
                        due_date="2024-01-31", currency="USD")
    items = [LineItem(quantity=D(2), unit_price=D("25"), amount=D("50")), LineItem(quantity=D(1), unit_price=D(50), amount=D(50))]
    checks = {c.name: c.passed for c in run_checks(typed, items, err)}
    assert checks == {"line_items_sum": True, "line_item_rows": True, "total_arithmetic": True, "tax_rate": True,
                      "invoice_date_range": True, "due_after_issue": True, "currency_code": True}


def test_checks_catch_inconsistencies():
    typed, err = _typed(subtotal="100", tax_amount="10", total="120", invoice_date="2024-02-01", due_date="2024-01-02")
    items = [LineItem(quantity=D(1), unit_price=D(90), amount=D(90))]
    failed = {c.name for c in run_checks(typed, items, err) if c.passed is False}
    assert failed == {"line_items_sum", "total_arithmetic", "due_after_issue"}


def test_total_arith_not_applicable_when_tax_unknown():
    typed, err = _typed(subtotal="100", total="110")
    c = [c for c in run_checks(typed, [], err) if c.name == "total_arithmetic"][0]
    assert c.passed is None


def test_type_line_items_drops_empty_rows():
    raw = RawInvoice.model_validate({"line_items": [{"description": "Widget", "quantity": "2", "amount": "$10.00"},
                                                    {"description": None, "amount": None}]})
    items = type_line_items(raw)
    assert len(items) == 1 and items[0].quantity == D(2) and items[0].amount == D("10.00")


def test_grounding():
    text = "INVOICE # INV-2041\nDate: 03/05/2024\nACME Corp\nTotal Due $1,234.50"
    assert ground_value("total", D("1234.50"), "$1,234.50", text) == 1.0
    assert ground_value("total", D("9999.00"), "9999", text) == 0.0
    assert ground_value("invoice_number", "INV-2041", None, text) == 1.0
    assert ground_value("vendor_name", "ACME Corp", None, text) > 0.9
    assert ground_value("invoice_date", date(2024, 5, 3), "03/05/2024", text) > 0.9
