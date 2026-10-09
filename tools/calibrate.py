"""Fit confidence fusion on the *calib* split of a run and pick the abstain threshold.

    python -m tools.calibrate outputs/runs/<run> [--target-precision 0.98] [--write]

Uses the signals stored per field in field_results.jsonl, so no model calls are needed. Reports
ECE / AUROC on the held-out *test* split before vs after fitting, then (with --write) saves
docext/calibration.json, which the extractor loads at startup.

Threshold rule: the lowest threshold whose emitted values reach --target-precision on the calib split
(i.e. "abstain rather than be wrong more than 2% of the time"), which makes the
coverage/accuracy trade-off an explicit, reviewable product decision.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from docext.confidence import _PRIOR, CALIBRATION_FILE, FEATURES, feature_vector


def _xy(rows):
    X = np.array([feature_vector(r["signals"]) for r in rows])
    y = np.array([float(r["raw_correct"]) for r in rows])
    return X, y


def fit_logistic(X: np.ndarray, y: np.ndarray, l2: float = 1.0, iters: int = 3000, lr: float = 0.1) -> np.ndarray:
    """Plain L2-regularized logistic regression by gradient descent (tiny data; no sklearn dependency).
    The prior coefficients are the regularization centre, so sparse features stay near sensible values."""
    prior = np.array([_PRIOR[f] for f in FEATURES])
    w = prior.copy()
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ w))
        grad = X.T @ (p - y) / len(y) + l2 * (w - prior) / len(y)
        w -= lr * grad
    return w


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    e = 0.0
    for lo in np.linspace(0, 1, bins, endpoint=False):
        m = (p >= lo) & (p < lo + 1 / bins + (1e-9 if lo + 1 / bins >= 1 else 0))
        if m.any():
            e += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(e)


def auroc(p: np.ndarray, y: np.ndarray) -> float | None:
    pos, neg = p[y == 1], p[y == 0]
    if not len(pos) or not len(neg):
        return None
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())


def pick_threshold(p: np.ndarray, y: np.ndarray, target: float) -> tuple[float, float, float]:
    """Lowest threshold whose emitted precision >= target. Returns (threshold, precision, coverage)."""
    for t in np.round(np.arange(0.05, 0.96, 0.01), 2):
        m = p >= t
        if m.any() and y[m].mean() >= target:
            return float(t), float(y[m].mean()), float(m.mean())
    return 0.95, float(y[p >= 0.95].mean()) if (p >= 0.95).any() else 0.0, float((p >= 0.95).mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--target-precision", type=float, default=0.98)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rows = [json.loads(l) for l in (a.run / "field_results.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r.get("raw_correct") is not None and r.get("signals")]
    cal = [r for r in rows if r["split"] == "calib"]
    test = [r for r in rows if r["split"] == "test"]
    Xc, yc = _xy(cal)
    Xt, yt = _xy(test)
    prior = np.array([_PRIOR[f] for f in FEATURES])
    w = fit_logistic(Xc, yc)
    sig = lambda X, w: 1 / (1 + np.exp(-X @ w))  # noqa: E731
    self_t = Xt[:, 1]
    print(f"calib n={len(yc)} (acc {yc.mean():.3f})   test n={len(yt)} (acc {yt.mean():.3f})")
    print(f"{'':22}{'ECE(test)':>10}{'AUROC(test)':>13}")
    for name, p in (("model self-conf", self_t), ("prior fusion", sig(Xt, prior)), ("fitted fusion", sig(Xt, w))):
        au = auroc(p, yt)
        print(f"{name:22}{ece(p, yt):>10.4f}{au if au is None else round(au, 4):>13}")
    t, prec, cov = pick_threshold(sig(Xc, w), yc, a.target_precision)
    pt = sig(Xt, w)
    mt = pt >= t
    print(f"threshold {t} -> calib precision {prec:.3f} @ coverage {cov:.3f}; "
          f"test precision {yt[mt].mean() if mt.any() else float('nan'):.3f} @ coverage {mt.mean():.3f}")
    print("coef:", {f: round(float(x), 3) for f, x in zip(FEATURES, w)})
    if a.write:
        out = {"version": f"fit-{a.run.name}", "fitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "fitted_on": str(a.run.as_posix()), "n_calib": len(yc), "target_precision": a.target_precision,
               "abstain_threshold": t, "coef": {f: round(float(x), 4) for f, x in zip(FEATURES, w)},
               "test_metrics": {"ece": round(ece(pt, yt), 4), "auroc": auroc(pt, yt)}}
        CALIBRATION_FILE.write_text(json.dumps(out, indent=1) + "\n")
        print(f"wrote {CALIBRATION_FILE}")


if __name__ == "__main__":
    main()
