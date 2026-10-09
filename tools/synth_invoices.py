"""Synthetic stress invoices with *exact, full-schema* ground truth.

Why: the public benchmark labels only ~9 fields. This set covers the rest of the schema (bill-to vs
ship-to roles, PO, tax ids, terms, discount, tax rate, qty/unit price) and plants controlled traps:
  * absent_*      : optional fields deliberately NOT printed (hallucination probes)
  * table_split   : line-item table continues across pages with "continued" headers
  * decoy         : a "Previous balance" / "Amount paid" near the total that must not be read as total
  * locale        : US / EU (1.234,56 + DD.MM.YYYY) / ID (Rp 1.234.567) / UK formats
  * scan          : rendered to image, then rotated, blurred, noised, JPEG'd, saved as image-only PDF

    python -m tools.synth_invoices --n 12 --seed 7
"""
from __future__ import annotations

import argparse
import io
import json
import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from PIL import Image, ImageFilter
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT_DOCS = ROOT / "eval/data/docs/synth"
OUT_GT = ROOT / "eval/data/gt"
Q = Decimal("0.01")

VENDORS = {
    "EU": [("Borealis Lab Instruments GmbH", "Industriestr. 14, 70565 Stuttgart, Germany", "DE298374651"),
           ("Studio Vermeer B.V.", "Prinsengracht 263, 1016 GV Amsterdam, Netherlands", "NL854502130B01")],
    "ID": [("PT Sinar Nusantara Teknik", "Jl. Gatot Subroto No. 88, Jakarta Selatan 12930, Indonesia",
            "01.234.567.8-901.000"),
           ("CV Kopi Lereng Merapi", "Jl. Kaliurang Km 9, Sleman, Yogyakarta 55581, Indonesia", "82.415.903.6-542.000")],
    "US": [("Cobalt Ridge Software LLC", "2201 Market St, Suite 400, Denver, CO 80205, USA", "84-2918377"),
           ("Mariposa Coffee Roasters", "455 Alameda St, Los Angeles, CA 90013, USA", "95-4410287")],
    "UK": [("Thistle & Pine Joinery Ltd", "7 Canal Wharf, Leeds LS11 5PS, United Kingdom", "GB 318 4421 77"),
           ("Halden Marine Electronics Ltd", "Unit 4, Ocean Quay, Southampton SO14 3JP, United Kingdom",
            "GB 762 0193 54")],
}
CUSTOMERS = [
    ("Hollander Medical Group", "88 Weteringschans, 1017 SH Amsterdam, Netherlands"),
    ("Kestrel Aviation Services", "Hangar 3, Bristol Airport, Bristol BS48 3DY, United Kingdom"),
    ("CV Maju Bersama", "Jl. Diponegoro 21, Bandung 40115, Indonesia"),
    ("Ridgeway Public Schools", "1400 Ridgeway Ave, Portland, OR 97214, USA"),
    ("Atelier Lumen SARL", "12 Rue des Arts, 69002 Lyon, France"),
]
WAREHOUSES = [("Kestrel Aviation - Stores", "Unit 9, Lulsgate Business Park, Bristol BS48 3DZ, United Kingdom"),
              ("Ridgeway Central Warehouse", "77 NE Columbia Blvd, Portland, OR 97211, USA")]
ITEMS = ["Calibration service, pressure gauge", "Stainless fitting 1/4in NPT", "Annual software license (seat)",
         "Oak worktop 3000x600x40mm", "Onsite installation (hours)", "Ethiopian Yirgacheffe 1kg", "Thermocouple type K",
         "Laboratory glove nitrile (box 100)", "Cloud storage 1TB / month", "Consulting - solution design (hours)",
         "Ceramic pour-over dripper", "Hinge, soft close, pair", "Data logger USB, 8ch", "Freight & insurance pallet"]

LOCALES = {
    "US": dict(cur="USD", sym="$", fmt_money=lambda d: f"${d:,.2f}", fmt_date=lambda x: x.strftime("%m/%d/%Y"),
               page=LETTER, tax_label="Sales Tax", rate=Decimal("8.25")),
    "EU": dict(cur="EUR", sym="€", fmt_money=lambda d: f"{d:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
               fmt_date=lambda x: x.strftime("%d.%m.%Y"), page=A4, tax_label="MwSt.", rate=Decimal("19")),
    "ID": dict(cur="IDR", sym="Rp", fmt_money=lambda d: "Rp " + f"{d:,.0f}".replace(",", "."),
               fmt_date=lambda x: x.strftime("%d/%m/%Y"), page=A4, tax_label="PPN", rate=Decimal("11")),
    "UK": dict(cur="GBP", sym="£", fmt_money=lambda d: f"£{d:,.2f}", fmt_date=lambda x: x.strftime("%d %b %Y"),
               page=A4, tax_label="VAT", rate=Decimal("20")),
}


@dataclass
class Spec:
    doc_id: str
    locale: str
    n_items: int
    layout: str  # classic | modern | compact
    absent: set[str]
    ship_to: bool
    discount: bool
    decoy: bool
    scan: str | None  # None | light | heavy


def build_invoice(spec: Spec, rng: random.Random) -> dict:
    L = LOCALES[spec.locale]
    v = rng.choice(VENDORS[spec.locale])
    c = rng.choice(CUSTOMERS)
    inv_date = date(2025, 1, 1) + timedelta(days=rng.randint(0, 500))
    is_idr = L["cur"] == "IDR"
    items = []
    for _ in range(spec.n_items):
        qty = Decimal(rng.choice([1, 1, 2, 3, 5, 10, 12, 25]))
        price = Decimal(rng.randint(15, 4_500) * 1000) if is_idr else Decimal(rng.randint(250, 250_000)) / 100
        price = price.quantize(Q)
        items.append({"description": rng.choice(ITEMS), "quantity": qty, "unit_price": price,
                      "amount": (qty * price).quantize(Q, ROUND_HALF_UP)})
    subtotal = sum((i["amount"] for i in items), Decimal(0))
    discount = (subtotal * Decimal(rng.choice([5, 10])) / 100).quantize(Q, ROUND_HALF_UP) if spec.discount else None
    base = subtotal - (discount or 0)
    tax = (base * L["rate"] / 100).quantize(Q, ROUND_HALF_UP)
    total = base + tax
    terms_days = rng.choice([14, 30, 45])
    f = {
        "document_type": "invoice",
        "invoice_number": rng.choice(["INV-", "", "SI/", "F"]) + f"{inv_date.year}-{rng.randint(100, 99999):05d}",
        "invoice_date": inv_date.isoformat(),
        "due_date": (inv_date + timedelta(days=terms_days)).isoformat(),
        "currency": L["cur"],
        "po_number": f"PO-{rng.randint(10000, 99999)}",
        "payment_terms": f"Net {terms_days}",
        "vendor_name": v[0], "vendor_address": v[1], "vendor_tax_id": v[2],
        "bill_to_name": c[0], "bill_to_address": c[1],
        "ship_to_name": None, "ship_to_address": None,
        "subtotal": subtotal, "discount": discount, "tax_rate": L["rate"], "tax_amount": tax, "total": total,
    }
    if spec.ship_to:
        w = rng.choice(WAREHOUSES)
        f["ship_to_name"], f["ship_to_address"] = w
    for k in spec.absent:
        f[k] = None
    return {"fields": f, "items": items}


# ------------------------------------------------------------------ rendering
def render_pdf(spec: Spec, inv: dict) -> bytes:
    L = LOCALES[spec.locale]
    f, items = inv["fields"], inv["items"]
    m = L["fmt_money"]
    W, H = L["page"]
    buf = io.BytesIO()
    cv = canvas.Canvas(buf, pagesize=L["page"])
    rows_first, rows_next = (14, 30) if spec.layout != "compact" else (18, 36)
    pages = [items[:rows_first]]
    rest = items[rows_first:]
    while rest:
        pages.append(rest[:rows_next])
        rest = rest[rows_next:]
    npages = len(pages)

    def header(pg: int):
        if spec.layout == "modern":
            cv.setFillColorRGB(0.12, 0.24, 0.42)
            cv.rect(0, H - 90, W, 90, fill=1, stroke=0)
            cv.setFillColorRGB(1, 1, 1)
            cv.setFont("Helvetica-Bold", 20)
            cv.drawString(40, H - 50, f["vendor_name"] or "")
            cv.setFont("Helvetica", 9)
            cv.drawString(40, H - 68, f["vendor_address"] or "")
            cv.setFont("Helvetica-Bold", 26)
            cv.drawRightString(W - 40, H - 55, "INVOICE")
            cv.setFillColorRGB(0, 0, 0)
        else:
            font = "Times-Bold" if spec.layout == "classic" else "Courier-Bold"
            cv.setFont(font, 16)
            cv.drawCentredString(W / 2, H - 50, f["vendor_name"] or "")
            cv.setFont(font.replace("-Bold", "-Roman" if "Times" in font else ""), 9)
            cv.drawCentredString(W / 2, H - 64, f["vendor_address"] or "")
            if f["vendor_tax_id"]:
                cv.drawCentredString(W / 2, H - 76, f"Tax ID: {f['vendor_tax_id']}")
            cv.setFont(font, 14)
            cv.drawString(40, H - 105, "TAX INVOICE" if spec.locale in ("UK", "ID") else "INVOICE")
        cv.setFont("Helvetica", 8)
        cv.drawRightString(W - 40, 30, f"Page {pg} of {npages}")
        if pg > 1:
            cv.setFont("Helvetica-Oblique", 9)
            cv.drawString(40, H - 120, f"Invoice {f['invoice_number'] or ''} (continued)")

    def meta_block():
        y = H - 130
        cv.setFont("Helvetica", 9)
        rows = [("Invoice No.", f["invoice_number"]), ("Invoice Date", _d(L, f["invoice_date"])),
                ("Due Date", _d(L, f["due_date"])), ("PO Number", f["po_number"]), ("Terms", f["payment_terms"])]
        if spec.layout == "modern" and f["vendor_tax_id"]:
            rows.append(("VAT/Tax No.", f["vendor_tax_id"]))
        for label, val in rows:
            if val:
                cv.drawRightString(W - 150, y, label + ":")
                cv.drawString(W - 145, y, str(val))
                y -= 13
        # parties
        y2 = H - 130
        cv.setFont("Helvetica-Bold", 9)
        cv.drawString(40, y2, "BILL TO")
        cv.setFont("Helvetica", 9)
        cv.drawString(40, y2 - 12, f["bill_to_name"] or "")
        for i, part in enumerate(_wrap(f["bill_to_address"] or "", 45)):
            cv.drawString(40, y2 - 24 - 11 * i, part)
        if f["ship_to_name"]:
            cv.setFont("Helvetica-Bold", 9)
            cv.drawString(230, y2, "SHIP TO")
            cv.setFont("Helvetica", 9)
            cv.drawString(230, y2 - 12, f["ship_to_name"])
            for i, part in enumerate(_wrap(f["ship_to_address"], 35)):
                cv.drawString(230, y2 - 24 - 11 * i, part)
        return min(y, y2 - 70) - 20

    def table(rows, y):
        cols = [40, W - 300, W - 220, W - 130]
        cv.setFont("Helvetica-Bold", 9)
        if spec.layout != "compact":
            cv.setFillColorRGB(0.9, 0.9, 0.9)
            cv.rect(36, y - 4, W - 72, 15, fill=1, stroke=0)
            cv.setFillColorRGB(0, 0, 0)
        cv.drawString(cols[0], y, "Description")
        cv.drawRightString(cols[1] + 30, y, "Qty")
        cv.drawRightString(cols[2] + 40, y, "Unit Price")
        cv.drawRightString(W - 40, y, "Amount")
        y -= 16
        cv.setFont("Helvetica", 9)
        for it in rows:
            cv.drawString(cols[0], y, it["description"])
            cv.drawRightString(cols[1] + 30, y, f"{it['quantity']}")
            cv.drawRightString(cols[2] + 40, y, m(it["unit_price"]))
            cv.drawRightString(W - 40, y, m(it["amount"]))
            if spec.layout == "classic":
                cv.setStrokeColorRGB(0.8, 0.8, 0.8)
                cv.line(36, y - 4, W - 36, y - 4)
            y -= 15
        return y

    for pi, rows in enumerate(pages, 1):
        header(pi)
        y = meta_block() if pi == 1 else H - 145
        y = table(rows, y)
        if pi < npages:
            cv.setFont("Helvetica-Oblique", 8)
            cv.drawRightString(W - 40, y - 6, "Continued on next page...")
            cv.showPage()
    # totals block
    y -= 15
    tot = [("Subtotal", f["subtotal"])]
    if f["discount"]:
        tot.append(("Discount", -f["discount"]))
    if f["tax_amount"] is not None:
        lbl = L["tax_label"] + (f" {f['tax_rate']}%" if f["tax_rate"] is not None else "")
        tot.append((lbl, f["tax_amount"]))
    tot.append(("TOTAL DUE", f["total"]))
    for label, val in tot:
        cv.setFont("Helvetica-Bold" if label == "TOTAL DUE" else "Helvetica", 10)
        cv.drawRightString(W - 150, y, label)
        cv.drawRightString(W - 40, y, ("-" if val < 0 else "") + m(abs(val)))
        y -= 15
    if spec.decoy:
        cv.setFont("Helvetica", 8)
        prev = (f["total"] * Decimal("0.37")).quantize(Q)
        cv.drawString(40, y - 10, f"Account summary: previous balance {m(prev)}, payments received {m(prev)}, "
                                  "balance brought forward " + m(Decimal(0)))
    cv.setFont("Helvetica", 8)
    cv.drawString(40, 50, "Thank you for your business. Please quote the invoice number with your payment.")
    cv.save()
    return buf.getvalue()


def _d(L, iso):
    return L["fmt_date"](date.fromisoformat(iso)) if iso else None


def _wrap(s: str, n: int) -> list[str]:
    out, cur = [], ""
    for w in s.split(", "):
        if cur and len(cur) + len(w) + 2 > n:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur}, {w}" if cur else w
    return out + ([cur] if cur else [])


def degrade(pdf: bytes, level: str, rng: random.Random) -> bytes:
    """Rasterize and simulate a scanner/phone: rotation, blur, noise, contrast loss, JPEG; image-only PDF."""
    import numpy as np
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf)
    imgs = []
    for i in range(len(doc)):
        im = doc[i].render(scale=(130 if level == "heavy" else 170) / 72).to_pil().convert("L")
        im = im.rotate(rng.uniform(-2.5, 2.5) if level == "heavy" else rng.uniform(-1, 1), expand=True, fillcolor=255)
        im = im.filter(ImageFilter.GaussianBlur(1.1 if level == "heavy" else 0.5))
        a = np.asarray(im).astype(np.float32)
        a = a * (0.8 if level == "heavy" else 0.92) + (30 if level == "heavy" else 10)
        a += np.random.default_rng(rng.randint(0, 10**6)).normal(0, 14 if level == "heavy" else 6, a.shape)
        im = Image.fromarray(a.clip(0, 255).astype("uint8"))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=35 if level == "heavy" else 65)
        imgs.append(Image.open(io.BytesIO(b.getvalue())).convert("RGB"))
    doc.close()
    out = io.BytesIO()
    imgs[0].save(out, "PDF", save_all=True, append_images=imgs[1:], resolution=150)
    return out.getvalue()


SPECS = [
    # doc_id, locale, n_items, layout, absent, ship_to, discount, decoy, scan
    ("synth-01-us-basic", "US", 4, "classic", set(), False, False, False, None),
    ("synth-02-eu-shipto", "EU", 6, "modern", {"po_number"}, True, False, False, None),
    ("synth-03-id-scan", "ID", 5, "classic", {"due_date", "po_number"}, False, False, False, "light"),
    ("synth-04-uk-discount", "UK", 7, "compact", {"payment_terms"}, True, True, False, None),
    ("synth-05-us-multipage", "US", 34, "classic", set(), True, True, False, None),
    ("synth-06-eu-multipage-scan", "EU", 40, "modern", {"due_date"}, False, False, False, "heavy"),
    ("synth-07-us-decoy", "US", 5, "modern", {"po_number", "vendor_tax_id"}, False, False, True, None),
    ("synth-08-id-heavyscan", "ID", 9, "compact", {"payment_terms", "po_number"}, True, True, False, "heavy"),
    ("synth-09-uk-minimal", "UK", 2, "classic", {"due_date", "po_number", "payment_terms", "tax_rate"}, False, False,
     False, None),
    ("synth-10-us-multipage-decoy", "US", 52, "compact", {"vendor_tax_id"}, True, False, True, "light"),
    ("synth-11-eu-no-tax-id", "EU", 3, "classic", {"vendor_tax_id", "po_number", "due_date"}, False, True, False, "light"),
    ("synth-12-id-multipage", "ID", 22, "modern", set(), True, False, True, None),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    OUT_DOCS.mkdir(parents=True, exist_ok=True)
    for row in SPECS:
        spec = Spec(*row)
        rng = random.Random(f"{args.seed}-{spec.doc_id}")
        inv = build_invoice(spec, rng)
        pdf = render_pdf(spec, inv)
        if spec.scan:
            pdf = degrade(pdf, spec.scan, rng)
        (OUT_DOCS / f"{spec.doc_id}.pdf").write_bytes(pdf)
        import pypdfium2 as pdfium
        npages = len(pdfium.PdfDocument(pdf))
        tags = ["synthetic", f"locale:{spec.locale}", f"layout:{spec.layout}"]
        tags += ["multipage", "table_split"] if npages > 1 else []
        tags += [f"scan:{spec.scan}", "image"] if spec.scan else []
        tags += ["absent_fields"] if spec.absent or not spec.ship_to else []
        tags += ["ship_to"] if spec.ship_to else []
        tags += ["decoy_amounts"] if spec.decoy else []
        fields = {k: (str(v) if isinstance(v, Decimal) else v) for k, v in inv["fields"].items()}
        gt = {
            "doc_id": spec.doc_id, "file": f"docs/synth/{spec.doc_id}.pdf", "source": "synthetic",
            "license": "generated (this repo)", "label_provenance": "exact by construction (tools/synth_invoices.py)",
            "pages": npages, "tags": tags,
            "description": f"{spec.locale} {spec.layout} invoice, {spec.n_items} items, absent={sorted(spec.absent)}",
            "fields": fields,
            "line_items": [{k: (str(v) if isinstance(v, Decimal) else v) for k, v in it.items()} for it in inv["items"]],
            "line_item_cells": ["description", "quantity", "unit_price", "amount"],
            "should_flag": False, "notes": "",
        }
        (OUT_GT / f"{spec.doc_id}.json").write_text(json.dumps(gt, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(spec.doc_id, npages, "pages")


if __name__ == "__main__":
    main()
