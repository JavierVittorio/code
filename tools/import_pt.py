"""Import 17 REAL phone photos of Portuguese invoices (faturas / faturas-recibo) from InvoicesReceiptsPT
(Apache-2.0, Francisco-Cruz on Hugging Face; https://zenodo.org/records/7213544).

    python -m tools.import_pt

Why these: real thermal-paper photos (faded print, curl, staples, punch holes, handwritten ticks), a
different layout culture from the rest of the set, Portuguese labels, DD/MM dates, VAT-inclusive pricing,
legal-entity vs trade-name vendors, and "decoy" totals (Total Ilíquido, Total s/ Desconto).

Ground truth: the dataset's human transcriptions were NOT taken on trust. Every label below was checked
against the photo (see eval/data/GT_CHANGELOG.md). Fields the dataset does not annotate (subtotal, VAT rate,
customer, line items) were added only where clearly printed. Deliberate choices:
  * vendor_name: the issuing legal entity as printed, with the trade name as an accepted alternative
  * vendor_tax_id: corrected where the dataset label fails the Portuguese NIF mod-11 checksum AND the photo
    shows the corrected digits; left unlabeled where the dataset value is not the seller's NIF
  * fields that are ambiguous on the document (e.g. subtotal with mixed discounts) are left unlabeled
  * one document (a pharmacy receipt) was excluded: it carries a private individual's name and home address
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://huggingface.co/datasets/Francisco-Cruz/InvoicesReceiptsPT/resolve/main/"
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "eval/data/docs/pt"
GT = ROOT / "eval/data/gt"


def li(desc, qty=None, unit=None, amount=None):
    return {"description": desc, "quantity": qty, "unit_price": unit, "amount": amount}


# stem -> (fields, alt_values, line_items or None, cells, extra tags, notes)
DOCS_PT: dict[str, dict] = {
    "20210215_162717": dict(
        fields={"vendor_name": "Bimba y Lola", "invoice_number": "FT TP40/20009879", "invoice_date": "2020-11-17",
                "subtotal": "103.25", "tax_rate": "23", "tax_amount": "23.75", "total": "127.00"},
        items=[li("JERSEY DE PUNTO", 1, "52.00", "52.00"), li("JERSEY DE PUNTO", 1, "75.00", "75.00")],
        notes="dataset nif_seller 502586745 is the billing-software maker's NIF printed in the footer, not the "
              "seller's -> vendor_tax_id left unlabeled. Two-digit year date (17/11/20)."),
    "20210322_161042": dict(
        fields={"vendor_name": "WORTEN Equipamentos para o Lar SA", "vendor_tax_id": "503630330",
                "invoice_number": "FT 8TA109/012049", "invoice_date": "2019-07-21", "bill_to_name": "FLIKEHOME ALGARVE LDA",
                "subtotal": "8.12", "tax_rate": "23", "tax_amount": "1.87", "total": "9.99"},
        alts={"vendor_name": ["Worten"], "vendor_tax_id": ["PT503630330"]},
        items=[li("CABO MICRO-USB 2.0 GOODIS", None, None, "9.99")], cells=["description", "amount"]),
    "20210323_173242": dict(
        fields={"vendor_name": "IKEA Portugal, Moveis e Decoracao Lda", "vendor_tax_id": "505416654",
                "invoice_number": "FAC 45300720190064/735", "invoice_date": "2019-07-16",
                "bill_to_name": "FLIKEHOME ALGARVE, LDA", "subtotal": "96.49", "tax_rate": "23", "tax_amount": "22.19",
                "total": "118.68"},
        alts={"vendor_name": ["IKEA", "IKEA Loule"]},
        items=[li("GOKART prot clch 160x200", 2, "12.99", "25.98"), li("GOKART prot clch 90x200", 4, "8.00", "32.00"),
               li("INDIRA NN colcha 150x250 branco", 4, "15.00", "60.00"), li("FRAKTA saco, grd 71 l azul", None, None, "0.70")],
        tags=["label_corrected"],
        notes="dataset nif_seller 505116054 fails the NIF checksum; photo shows 505416654 (valid)."),
    "20210323_194951": dict(
        fields={"vendor_name": "BCM Bricolage, SA", "vendor_tax_id": "506848558", "invoice_number": "FT 05390111/0126862",
                "invoice_date": "2019-02-03", "bill_to_name": "FLH Algarve LDA", "subtotal": "9.73", "tax_rate": "23",
                "tax_amount": "2.24", "total": "11.97"},
        alts={"vendor_name": ["AKI", "AKI Portimao"]},
        items=[li("2 REDUTORES E27/E14 PLAST", None, None, "1.99"), li("BASE C MESA QUAD 40W E14 P", 2, "4.99", "9.98")]),
    "20210324_162353": dict(
        fields={"vendor_name": "Norauto Portugal S.A.", "vendor_tax_id": "503629995", "invoice_number": "FT 060600003/332060",
                "invoice_date": "2019-02-24", "subtotal": "18.24", "tax_rate": "23", "tax_amount": "4.21", "total": "22.45"},
        alts={"vendor_name": ["Norauto"]},
        items=[li("5L NORAUTO 15W40 D", 1, "14.95", "14.95"), li("1LAMPADA NORAUTO H4", 1, "6.50", "6.50"),
               li("LIMPA VIDROS VELOX 50ML", 1, "1.00", "1.00")]),
    "20210324_162552": dict(
        fields={"vendor_name": "Ferragens G Lemos, Lda", "vendor_tax_id": "501378723", "invoice_number": "FT POS19V12/1903880",
                "invoice_date": "2019-02-26", "bill_to_name": "FLIKEHOME MEDIACAO IMOBILIA", "subtotal": "7.73",
                "tax_rate": "23", "tax_amount": "1.78", "total": "9.51"},
        items=[li("BROCA DEWALT SDS DT9532 3 10X8mm", 1, None, "9.51")],
        tags=["label_corrected", "faded"],
        notes="heavily faded thermal print. dataset nif_seller 501375723 fails the NIF checksum; photo shows "
              "501378723 (valid). Customer name is truncated on the paper; GT keeps it as printed."),
    "20210324_195741": dict(
        fields={"vendor_name": "Drogaria S Marcal Lda", "vendor_tax_id": "500563381", "invoice_number": "FR 001/12446",
                "invoice_date": "2019-03-14", "bill_to_name": "Flikehome", "subtotal": "2.28", "tax_rate": "23",
                "tax_amount": "0.52", "total": "2.80"},
        items=[li("Dobradica copo", 2, "1.40", "2.80")]),
    "20210428_143506": dict(
        fields={"vendor_name": "Supermercado Rocha S.A.", "vendor_tax_id": "500403201", "invoice_number": "FT 20192002/38",
                "invoice_date": "2019-02-09", "bill_to_name": "FLIKEHOME", "subtotal": "6.736", "tax_rate": "6",
                "tax_amount": "0.404", "total": "7.14"},
        items=[li("SCHAR PAO FORMA S.G CEREAIS 300G", 1, "3.57", "3.57"), li("SCHAR PAO FORMA S.G CEREAIS 300G", 1, "3.57", "3.57")],
        tags=["label_corrected", "faded"],
        notes="VAT printed with 3 decimals (0.404, base 6.736); compared at 2 dp. dataset nif_seller 500402201 fails "
              "the NIF checksum; photo shows 500403201 (valid)."),
    "20210322_161246": dict(
        fields={"vendor_name": "INTERMARCHE LAGOA PO", "vendor_tax_id": "259318329", "invoice_number": "FT F/0000021",
                "invoice_date": "2019-07-05", "bill_to_name": "Flakehome Algarve", "discount": "56.05", "tax_rate": "23",
                "tax_amount": "41.92", "total": "224.20"},
        alts={"vendor_name": ["Intermarche", "Bruno Filipe Carvalho Morgado"], "vendor_tax_id": ["PT259318329"]},
        items=[li("CHAVE PONTOS", 7, "14.90", "83.44"), li("CHAVE CRUCIFORM", 8, "9.50", "60.80"),
               li("CHAVE GORJA", 1, "4.95", "3.96"), li("CHAVE PALHETA", 2, "12.20", "19.52"),
               li("CHAVE COLORIDA", 3, "3.25", "7.80"), li("RE-3D", 1, "5.50", "4.40"), li("SOF1/2", 1, "6.60", "5.28"),
               li("CHAVE SIMPLES", 25, "1.95", "39.00")],
        notes="sole-trader vendor (legal name is a person) trading as Intermarche. Line amounts include a 20% "
              "discount so qty x unit != amount by design. 'S/ Desconto 280,25' is a decoy; subtotal left unlabeled "
              "(pre-discount gross vs net base 182,28 is ambiguous for this layout)."),
    "20210323_171146": dict(
        fields={"vendor_name": "GESPOST Gestao e Administracao de Postos de Abastecimento Unipessoal Lda",
                "vendor_tax_id": "503769959", "invoice_number": "FR 4371TPV3/390007838", "invoice_date": "2019-07-15",
                "bill_to_name": "FLIKEHOME ALGARVE, LDA", "subtotal": "25.63", "tax_rate": "23", "tax_amount": "5.90",
                "total": "31.53"},
        alts={"vendor_name": ["Repsol", "ES Repsol Portimao"]},
        notes="fuel station run by an operator company; card-terminal slip with a second (zero) NIF below."),
    "20210428_153616": dict(
        fields={"vendor_name": "CTT - Correios de Portugal, SA", "vendor_tax_id": "500077568",
                "invoice_number": "FR CTT2019FR881074701/1235", "invoice_date": "2019-03-04", "bill_to_name": "FLIKE HOME LDA",
                "subtotal": "5.00", "tax_amount": "0.16", "total": "5.16"},
        alts={"vendor_name": ["CTT"]},
        items=[li("Reg. Int. RH336508169PT", 1, None, "4.30"), li("SAQUETAS ALMOFADADAS", 1, None, "0.70")],
        notes="mixed 0% (exempt postal service) and 23% VAT -> tax_rate left unlabeled."),
    "20210428_182133": dict(
        fields={"vendor_name": "Carvalho, Batista, Lda", "vendor_tax_id": "500537380", "invoice_number": "FT 2019A17/2560",
                "invoice_date": "2019-04-09", "bill_to_name": "FLIKEHOME LDA", "subtotal": "5.29", "tax_rate": "23",
                "tax_amount": "1.22", "total": "6.51"},
        items=[li("Lampada Philips Tld 18", 1, "5.29", "5.29")],
        notes="decoy number 'Num. 2560 - 17' printed next to the real invoice number."),
    "20210428_183355": dict(
        fields={"vendor_name": "Casa Bernardino", "vendor_tax_id": "104110015", "invoice_number": "FR PA9/29",
                "invoice_date": "2019-03-25", "bill_to_name": "Flikehome", "subtotal": "36.99", "tax_rate": "23",
                "tax_amount": "8.51", "total": "45.50"},
        alts={"vendor_name": ["Maria Manuela Fernandes Campos"]},
        items=[li("CHAVE PONTOS", 3, "10.00", "30.00"), li("Chave universal", 7, "1.50", "10.50"),
               li("Chave 4 entradas", 1, "5.00", "5.00")]),
    "20210428_183626": dict(
        fields={"vendor_name": "Erilar", "vendor_tax_id": "124713491", "invoice_number": "FR 1/1072",
                "invoice_date": "2018-12-06", "bill_to_name": "FLIKEHOME", "subtotal": "47.97", "tax_rate": "23",
                "tax_amount": "11.03", "total": "59.00"},
        alts={"vendor_name": ["Maria Rosario Alves Almeida Pimenta"]},
        items=[li("CALORIFICO OLEO ORBEGOZO 2000W RF2000", 1, "59.00", "59.00")]),
    "20210428_191514": dict(
        fields={"vendor_name": "GALPGESTE, SA", "vendor_tax_id": "503043745", "invoice_number": "FR 1155475201911Avg/314",
                "invoice_date": "2019-03-01", "bill_to_name": None, "tax_rate": "23", "tax_amount": "2.86",
                "total": "15.28"},
        alts={"vendor_name": ["Galp"]},
        items=[li("GASOLINA EVOLOGIC 95", "9.68", "1.579", "15.28")],
        notes="customer block has only a NIF and a licence plate, no name -> bill_to_name verified absent "
              "(hallucination probe). Numeric date 01/03/2019 is DD/MM. Subtotal not printed -> unlabeled."),
    "20210429_220319": dict(
        fields={"vendor_name": "Consertos Rapidos Amoreiras, Lda", "vendor_tax_id": "506175502",
                "invoice_number": "FTR 31/6397", "invoice_date": "2019-11-05", "bill_to_name": "FLIKEHOME",
                "subtotal": "52.11", "tax_rate": "23", "tax_amount": "11.99", "total": "64.10"},
        alts={"vendor_name": ["Security Center", "Security Center Amoreiras"]},
        items=[li("CHAVE PONTOS MC148", 3, "17.90", "53.70"), li("CHAVE PLANA CS206 / CI-DL", 3, "2.60", "7.80"),
               li("CHAVE PLANA UL050 / U-5D", 1, "2.60", "2.60")],
        tags=["punch_holes", "handwriting_marks"]),
    "20210507_203411": dict(
        fields={"vendor_name": "COPIMATICA - Informatica e Copia, Servicos e Sistemas, Lda", "vendor_tax_id": "502431377",
                "invoice_number": "FTR 2/72069", "invoice_date": "2017-11-27", "bill_to_name": "FLIKEHOME LDA",
                "subtotal": "19.20", "tax_rate": "23", "tax_amount": "4.41", "total": "23.61"},
        alts={"vendor_name": ["Copimatica"]},
        items=[li("CARTOLINA IRIS A3(WHITE)", 6, "0.45", "2.70"), li("CARTOLINA IRIS A4(WHITE)", 1, "0.37", "0.37"),
               li("Fotocopias/Impressoes Cores A4", 26, "0.79", "20.54")],
        notes="decoy: 'Total Iliquido 23.61' (gross) printed above the net base 19.20."),
}


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    for stem, d in DOCS_PT.items():
        dest = DOCS / f"{stem}.jpg"
        if not dest.exists():
            for attempt in range(6):  # HF rate-limits bursts
                try:
                    urllib.request.urlretrieve(f"{BASE}1_Images/{stem}.jpg", dest)
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"retry {stem}: {e}", file=sys.stderr)
                    time.sleep(30)
        fields = {"document_type": "invoice", "currency": "EUR", **d["fields"]}
        gt = {
            "doc_id": f"pt-{stem}",
            "file": f"docs/pt/{stem}.jpg",
            "source": "invoices-receipts-pt",
            "license": "Apache-2.0 (Francisco-Cruz/InvoicesReceiptsPT)",
            "label_provenance": "dataset human transcription, every label verified against the photo; extra fields "
                                "annotated from the photo; corrections in GT_CHANGELOG.md",
            "pages": 1,
            "tags": ["real_photo", "non_english", "thermal_receipt", *d.get("tags", [])],
            "description": f"Real Portuguese invoice photo: {fields['vendor_name']}",
            "fields": fields,
            "alt_values": d.get("alts", {}),
            "line_items": d.get("items"),
            "line_item_cells": d.get("cells", ["description", "quantity", "unit_price", "amount"]),
            "should_flag": False,
            "notes": d.get("notes", ""),
        }
        (GT / f"{gt['doc_id']}.json").write_text(json.dumps(gt, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("ok", gt["doc_id"], file=sys.stderr)


if __name__ == "__main__":
    main()
