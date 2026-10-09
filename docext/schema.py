"""Field schema for invoice extraction.

Two layers:
  * Raw*  : what the model is asked to emit. Deliberately lenient (strings/numbers/nulls) so a
            slightly-off response can still be parsed and *then* validated, instead of failing hard.
  * Public: typed, normalized result returned by the API (Decimal money, ISO dates, per-field
            status + confidence + evidence).

The schema is flat (vendor_name, bill_to_name, ...) instead of nested parties. Party *roles* are
still explicit in the field names; flat keys make the prompt shorter and the eval simpler.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Kind(str, Enum):
    text = "text"  # free text, fuzzy-compared (names, addresses)
    ident = "ident"  # identifiers, exact-compared after normalization (invoice no., PO, tax id)
    date = "date"
    money = "money"
    rate = "rate"  # percentage, e.g. 10 for 10%
    currency = "currency"  # ISO 4217
    doctype = "doctype"  # invoice | credit_note


# Ordered: this is also the order presented to the model.
FIELD_SPECS: dict[str, tuple[Kind, str]] = {
    "document_type": (Kind.doctype, "'invoice' or 'credit_note' (credit note / credit memo / nota de credito)"),
    "invoice_number": (Kind.ident, "Invoice number / ID as printed"),
    "invoice_date": (Kind.date, "Issue date of the invoice"),
    "due_date": (Kind.date, "Payment due date. Only if explicitly printed; do NOT compute from terms"),
    "currency": (Kind.currency, "ISO 4217 code (USD, EUR, IDR, ...), inferred from symbols only if unambiguous"),
    "po_number": (Kind.ident, "Purchase order number, if printed"),
    "payment_terms": (Kind.text, "Payment terms text, e.g. 'Net 30'"),
    "vendor_name": (Kind.text, "Seller / supplier issuing the invoice"),
    "vendor_address": (Kind.text, "Seller address, single line, comma separated"),
    "vendor_tax_id": (Kind.ident, "Seller tax/VAT/GST/NPWP/EIN number"),
    "bill_to_name": (Kind.text, "Buyer / customer being billed"),
    "bill_to_address": (Kind.text, "Billing address, single line, comma separated"),
    "ship_to_name": (Kind.text, "Ship-to / deliver-to party, only if a separate ship-to block exists"),
    "ship_to_address": (Kind.text, "Ship-to address, only if a separate ship-to block exists"),
    "subtotal": (Kind.money, "Sum of line items before tax (and before invoice-level discount/charges)"),
    "discount": (Kind.money, "Total invoice-level discount amount (positive number)"),
    "other_charges": (Kind.money, "Sum of non-tax charges in the totals block: shipping, freight, delivery, handling, "
                                  "service fees, surcharges. Null if none printed"),
    "tax_rate": (Kind.rate, "Tax rate in percent (10 for 10%). Only if printed"),
    "tax_amount": (Kind.money, "Total tax amount"),
    "total": (Kind.money, "Final amount due / grand total"),
}
FIELD_NAMES = list(FIELD_SPECS)
MONEY_FIELDS = [k for k, (kind, _) in FIELD_SPECS.items() if kind == Kind.money]


# ---------------------------------------------------------------- raw (model output) layer
class _Lenient(BaseModel):
    model_config = ConfigDict(extra="ignore", coerce_numbers_to_str=False)


class RawField(_Lenient):
    value: str | float | int | None = None
    evidence: str | None = None
    page: int | None = None
    confidence: float | None = None


class RawLineItem(_Lenient):
    description: str | None = None
    quantity: str | float | int | None = None
    unit_price: str | float | int | None = None
    amount: str | float | int | None = None
    page: int | None = None


class RawInvoice(_Lenient):
    fields: dict[str, RawField] = Field(default_factory=dict)
    line_items: list[RawLineItem] = Field(default_factory=list)
    line_items_confidence: float | None = None
    notes: str | None = None


# ---------------------------------------------------------------- public (typed) layer
Status = Literal["extracted", "absent", "abstained"]


class ExtractedField(BaseModel):
    value: str | Decimal | date | None = None
    status: Status
    confidence: float = Field(ge=0.0, le=1.0)
    page: int | None = None
    evidence: str | None = None
    # Value as returned by the model (before normalization / abstention), kept for debugging + eval.
    raw_value: str | None = None
    # Features that fed the confidence score; used for calibration and failure triage.
    signals: dict[str, Any] = Field(default_factory=dict)


class LineItem(BaseModel):
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    amount: Decimal | None = None
    page: int | None = None


class Check(BaseModel):
    name: str
    passed: bool | None  # None = not applicable (inputs missing)
    detail: str = ""
    fields: list[str] = Field(default_factory=list)


class Usage(BaseModel):
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0  # actual billed (0 for :free models)
    list_cost_usd: float = 0.0  # list-price equivalent from config, for comparability
    latency_ms: float = 0.0
    cache_hit: bool = False


class ExtractionResult(BaseModel):
    doc_id: str
    status: Literal["ok", "failed"] = "ok"
    error: str | None = None
    # Document-level routing decision: send to a human when numbers don't reconcile or key fields abstained.
    needs_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    fields: dict[str, ExtractedField] = Field(default_factory=dict)
    line_items: list[LineItem] = Field(default_factory=list)
    line_items_confidence: float = 0.0
    checks: list[Check] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    meta: dict[str, Any] = Field(default_factory=dict)
