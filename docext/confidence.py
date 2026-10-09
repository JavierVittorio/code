"""Confidence fusion + abstention.

Model self-reported confidence alone is poorly calibrated (VLMs say 0.95 for almost everything). We
fuse it with signals we compute ourselves into P(correct) via a small logistic model:

    features: self_conf, grounding, n_checks_passed, n_checks_failed, reasked, format_ok

Coefficients are fit on a calibration split by `python -m tools.calibrate` (written to
calibration.json next to this file). Until then, hand-set priors are used. A field with fused
confidence below the abstain threshold is returned as status="abstained", value=null.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

FEATURES = ["bias", "self_conf", "grounding", "checks_passed", "checks_failed", "reasked", "format_ok"]
_PRIOR = {"bias": -3.0, "self_conf": 3.5, "grounding": 2.5, "checks_passed": 0.8, "checks_failed": -1.5,
          "reasked": -0.5, "format_ok": 1.0}
CALIBRATION_FILE = Path(__file__).with_name("calibration.json")


def load_coefficients(path: Path = CALIBRATION_FILE) -> tuple[dict[str, float], str]:
    try:
        d = json.loads(path.read_text())
        return {k: float(d["coef"][k]) for k in FEATURES}, d.get("version", "fitted")
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return dict(_PRIOR), "prior"


_COEF, COEF_VERSION = load_coefficients()


def feature_vector(sig: dict) -> list[float]:
    return [1.0, float(sig.get("self_conf", 0.5)), float(sig.get("grounding", 0.0)),
            min(float(sig.get("checks_passed", 0)), 2.0), min(float(sig.get("checks_failed", 0)), 2.0),
            float(bool(sig.get("reasked"))), float(bool(sig.get("format_ok", True)))]


def fuse(sig: dict, coef: dict[str, float] | None = None) -> float:
    c = coef or _COEF
    z = sum(c[f] * x for f, x in zip(FEATURES, feature_vector(sig)))
    return 1 / (1 + math.exp(-z))
