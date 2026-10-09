# Ground-truth changelog

Every change to `eval/data/gt/*.json` after import is recorded here: doc, field, old -> new, evidence.
A GT edit without an entry here is a bug: it changes the dataset hash and breaks comparability with
earlier runs.

| date | doc | field | old -> new | evidence / reason |
|---|---|---|---|---|
| 2026-10-09 | (all) | - | initial import | `tools/import_ipp.py` (benchmark answer keys, `scored` fields only) + `tools/synth_invoices.py` (exact by construction) |

Audits that led to **no** change (labels confirmed against the rendered page):
- 2026-10-09 triage of dev-v1-baseline: `ipp-photo-perspective-severe` invoice_date (page shows 02/08/2025 from a ZA
  vendor = 2 Aug, GT right), `ipp-photo-motion-blur-severe` invoice_date/total (the blurred page is not reliably
  legible even to a human reviewer; GT 2 August 2025 / £17,943.95 confirmed on `ipp-photo-crumple-severe`, a legible
  degradation of the same base invoice), `ipp-hard-missing-invoice-number-1` (no invoice number printed, only a
  delivery note number; GT null is right).

## 2026-10-09: import of 17 real Portuguese invoice photos (`tools/import_pt.py`)

Source labels are human transcriptions (InvoicesReceiptsPT, Apache-2.0). Each was checked against the photo
before import; additional fields (subtotal, VAT rate, customer, line items) were annotated from the photo only
where clearly printed. Disagreements with the source labels:

| doc | field | source label -> GT | evidence |
|---|---|---|---|
| pt-20210323_173242 (IKEA) | vendor_tax_id | 505116054 -> 505416654 | photo reads 505416654; source value fails the NIF mod-11 check digit, corrected one passes |
| pt-20210324_162552 (Ferragens G Lemos) | vendor_tax_id | 501375723 -> 501378723 | faded print reads 50137872 3; only 501378723 passes the check digit |
| pt-20210428_143506 (Supermercado Rocha) | vendor_tax_id | 500402201 -> 500403201 | photo reads 500403201; only it passes the check digit |
| pt-20210215_162717 (Bimba y Lola) | vendor_tax_id | 502586745 -> (unlabeled) | that number is the billing-software maker's NIF in the footer, not the seller's |
| all | vendor_name | brand name -> legal entity as printed, brand as alternative | e.g. "worten" -> "WORTEN Equipamentos para o Lar SA" (alt "Worten") |

Excluded: `20210509_001840` (Farmacia Gaspar). Its source label also has an error (`FR 0001/1064`, printed
`FR U001/1064`), but the receipt carries a private individual's full name and home address, so it is not
redistributed here.
