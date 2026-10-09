"""Local OCR used *only* for grounding (checking extracted values exist on the page), never for
extraction itself. RapidOCR (PaddleOCR models on ONNX runtime) is pip-only and CPU-friendly.
"""
from __future__ import annotations

import threading

import numpy as np

from .ingest import Page

_engine = None
_lock = threading.Lock()


def _get_engine():
    global _engine
    with _lock:
        if _engine is None:
            from rapidocr_onnxruntime import RapidOCR

            _engine = RapidOCR()
    return _engine


def page_text(page: Page) -> str:
    """Native text layer when the PDF has one, otherwise OCR (cached on the Page)."""
    if page.text_layer:
        return page.text_layer
    if page.ocr_text is None:
        img = page.image.convert("RGB")
        if max(img.size) > 2000:  # OCR accuracy plateaus; keep it fast
            s = 2000 / max(img.size)
            img = img.resize((round(img.width * s), round(img.height * s)))
        result, _ = _get_engine()(np.asarray(img))
        page.ocr_text = "\n".join(r[1] for r in (result or []))
    return page.ocr_text
