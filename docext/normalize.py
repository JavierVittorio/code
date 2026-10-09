"""Value normalizers shared by extraction (to type model output) and eval (to compare against GT).

Kept dependency-free and deterministic: every comparison in the scorecard goes through here, so a
change in this file is a change in the metric and is covered by tests.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

_CURRENCY_SYMBOLS = {
    "$": "USD", "US$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR", "Rp": "IDR",
    "RM": "MYR", "N$": "NAD", "S$": "SGD", "A$": "AUD", "C$": "CAD", "₩": "KRW", "₱": "PHP", "฿": "THB", "zł": "PLN",
}
_ISO_CODES = {
    "USD", "EUR", "GBP", "JPY", "INR", "IDR", "MYR", "SGD", "AUD", "CAD", "KRW", "PHP", "THB", "PLN",
    "CHF", "CNY", "HKD", "NZD", "SEK", "NOK", "DKK", "MXN", "BRL", "ZAR", "VND", "AED", "CZK", "HUF",
    "NAD", "ZMW", "BWP", "KES", "NGN", "EGP", "TRY", "ILS", "SAR", "TWD",
}


def parse_money(v: object) -> Decimal | None:
    """'$1,234.56' / '1.234,56 €' / '(12.00)' / 1234.5 -> Decimal('1234.56'). None if not a number."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float, Decimal)):
        return Decimal(str(v)).quantize(Decimal("0.01"))
    s = str(v).strip()
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-") or s.endswith("-")
    s = re.sub(r"[^\d.,]", "", s)
    if not re.search(r"\d", s):
        return None
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        thou = "." if dec == "," else ","
        s = s.replace(thou, "").replace(dec, ".")
    elif "," in s:
        # '1,234' thousands vs '12,50' decimal: decimal iff exactly 1-2 digits after a single comma
        parts = s.split(",")
        s = s.replace(",", ".") if len(parts) == 2 and 1 <= len(parts[1]) <= 2 else s.replace(",", "")
    elif s.count(".") > 1:
        parts = s.split(".")
        # '1.234.567' thousands; '1.234.56' -> last is decimal
        s = "".join(parts) if len(parts[-1]) == 3 else "".join(parts[:-1]) + "." + parts[-1]
    elif "." in s and len(s.split(".")[1]) == 3 and len(s.split(".")[0]) <= 3 and s.split(".")[0] != "0":
        # '1.234' is ambiguous; in invoices a 3-decimal money amount is rare -> thousands separator
        s = s.replace(".", "")
    try:
        d = Decimal(s).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None
    return -d if neg else d


def parse_number(v: object) -> Decimal | None:
    """Like parse_money but keeps precision (quantities, rates)."""
    m = parse_money(v)
    if m is None:
        return None
    if isinstance(v, (int, float)):
        return Decimal(str(v)).normalize()
    return m.normalize() if m == m.to_integral() else m


def parse_rate(v: object) -> Decimal | None:
    """'10%' / '10' / 0.1 -> Decimal('10'). Fractions <1 are interpreted as ratios."""
    n = parse_number(v)
    if n is None:
        return None
    if Decimal(0) < n < Decimal(1) and "%" not in str(v):
        n = n * 100
    return n.normalize()


_DATE_FORMATS = [
    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y",
    "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y", "%d-%b-%Y", "%d-%b-%y",
    "%d/%m/%y", "%m/%d/%y", "%d.%m.%y", "%b. %d, %Y", "%d %b, %Y", "%d %B, %Y",
]


def parse_date(v: object) -> date | None:
    """Prefer ISO (the model is told to emit ISO); fall back to common printed formats, day-first."""
    if v is None:
        return None
    if isinstance(v, date):
        return v
    s = re.sub(r"\s+", " ", str(v).strip()).replace("Sept", "Sep")
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", s)
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_currency(v: object) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if s.upper() in _ISO_CODES:
        return s.upper()
    return _CURRENCY_SYMBOLS.get(s) or (s.upper() if re.fullmatch(r"[A-Za-z]{3}", s) else None)


def parse_doctype(v: object) -> str | None:
    s = norm_text(v).replace(" ", "_")
    if s in ("invoice", "tax_invoice", "commercial_invoice"):
        return "invoice"
    if "credit" in s or s in ("nota_de_credito", "ndc"):
        return "credit_note"
    return None


def norm_text(v: object) -> str:
    """Casefold, strip accents/punctuation, collapse whitespace. For fuzzy text comparison."""
    if v is None:
        return ""
    s = unicodedata.normalize("NFKD", str(v))
    s = "".join(c for c in s if not unicodedata.combining(c)).casefold()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_ident(v: object) -> str:
    """Identifiers: drop everything but alphanumerics, uppercase. 'INV-00 12' == 'inv0012'."""
    if v is None:
        return ""
    return re.sub(r"[^0-9A-Za-z]", "", str(v)).upper()
