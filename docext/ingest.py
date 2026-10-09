"""Document ingest: PDF / image bytes -> list of page images (+ native text layer when present).

The image profile is the main cost/latency lever (vision tokens scale with pixels):
  * raw       : 200 DPI, color PNG, long side capped at 2400px      (baseline)
  * optimized : 150 DPI, grayscale + autocontrast, long side 1600px, JPEG q85, blank pages dropped
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field

import pypdfium2 as pdfium
from PIL import Image, ImageOps

PROFILES = {
    "raw": dict(dpi=200, max_side=2400, gray=False, fmt="PNG", quality=None, drop_blank=False),
    "optimized": dict(dpi=150, max_side=1600, gray=True, fmt="JPEG", quality=85, drop_blank=True),
}


@dataclass
class Page:
    index: int  # 1-based page number in the original document
    image: Image.Image
    text_layer: str = ""  # embedded PDF text, empty for scans
    ocr_text: str | None = None  # filled lazily by ocr.py
    meta: dict = field(default_factory=dict)

    def encoded(self, profile: str) -> tuple[str, str]:
        """Return (mime, base64) of the page image prepared for the model."""
        p = PROFILES[profile]
        img = self.image
        if p["gray"]:
            img = ImageOps.autocontrast(img.convert("L"), cutoff=1)
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img = _cap(img, p["max_side"])
        buf = io.BytesIO()
        if p["fmt"] == "JPEG":
            img.save(buf, "JPEG", quality=p["quality"], optimize=True)
            mime = "image/jpeg"
        else:
            img.save(buf, "PNG", optimize=True)
            mime = "image/png"
        return mime, base64.b64encode(buf.getvalue()).decode()


def _cap(img: Image.Image, max_side: int) -> Image.Image:
    w, h = img.size
    s = max_side / max(w, h)
    return img.resize((round(w * s), round(h * s)), Image.LANCZOS) if s < 1 else img


def _is_blank(img: Image.Image) -> bool:
    """Near-empty page (separator / back side of a scan): <0.3% dark pixels at thumbnail size."""
    g = img.convert("L").resize((200, int(200 * img.height / max(img.width, 1)) or 1))
    hist = g.histogram()
    dark = sum(hist[:160])
    return dark / max(sum(hist), 1) < 0.003


def sniff_kind(data: bytes, filename: str = "") -> str:
    if data[:5] == b"%PDF-" or filename.lower().endswith(".pdf"):
        return "pdf"
    return "image"


def load_pages(data: bytes, filename: str = "", profile: str = "optimized", max_pages: int = 8) -> list[Page]:
    p = PROFILES[profile]
    pages: list[Page] = []
    if sniff_kind(data, filename) == "pdf":
        pdf = pdfium.PdfDocument(data)
        try:
            for i in range(len(pdf)):
                page = pdf[i]
                img = page.render(scale=p["dpi"] / 72).to_pil()
                text = page.get_textpage().get_text_range() or ""
                pages.append(Page(index=i + 1, image=img, text_layer=text.strip()))
        finally:
            pdf.close()
    else:
        im = Image.open(io.BytesIO(data))
        for i in range(getattr(im, "n_frames", 1)):  # multi-frame TIFF = multi-page scan
            im.seek(i)
            pages.append(Page(index=i + 1, image=ImageOps.exif_transpose(im.copy()).convert("RGB")))

    total = len(pages)
    if p["drop_blank"]:
        kept = [pg for pg in pages if pg.text_layer or not _is_blank(pg.image)]
        pages = kept or pages[:1]
    if len(pages) > max_pages:
        # Invoices front-load header fields and back-load totals: keep head and tail pages.
        head = max_pages // 2
        pages = pages[:head] + pages[-(max_pages - head):]
    for pg in pages:
        pg.meta["total_pages"] = total
    return pages
