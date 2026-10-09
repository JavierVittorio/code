"""Fit confidence fusion on the *calib* split of a run and pick the abstain threshold.

    python -m tools.calibrate outputs/runs/<run> [--target-precision 0.98] [--write]

Uses the signals stored per field in field_results.jsonl, so no model calls are needed. Reports
ECE / AUROC on the held-out *test* split before vs after fitting, then (with --write) saves
docext/calibration.json, which the extractor loads at startup.

Regularization: L2 strength toward the hand-set prior is chosen by 5-fold cross-validated log-loss on
the calib split (with ~15 errors per split, an unregularized fit overfits; CV decides how far to move).

Threshold rule: minimize expected cost on the calib split, cost = C_err * (wrong values emitted) +
C_review * (fields abstained). Default C_err/C_review = 5 ("a silently wrong value costs five manual
checks"), which makes the coverage/accuracy trade-off an explicit, reviewable product decision.
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


def pick_threshold(p: np.ndarray, y: np.ndarray, cost_ratio: float) -> tuple[float, float, float]:
    """Threshold minimizing cost_ratio * errors_emitted + abstentions. Returns (threshold, precision, coverage)."""
    best = None
    for t in np.round(np.arange(0.0, 0.991, 0.01), 2):
        m = p >= t
        cost = cost_ratio * float(((y == 0) & m).sum()) + float((~m).sum())
        if best is None or cost < best[0] - 1e-9:
            best = (cost, float(t))
    t = best[1]
    m = p >= t
    return t, float(y[m].mean()) if m.any() else 0.0, float(m.mean())


def cv_l2(X: np.ndarray, y: np.ndarray, grid=(1, 3, 10, 30, 100, 300, 1000), k: int = 5, seed: int = 0) -> float:
    """Pick L2 strength by k-fold cross-validated log-loss (folds stratified by label)."""
    rng = np.random.default_rng(seed)
    folds = np.zeros(len(y), int)
    for cls in (0, 1):
        idx = rng.permutation(np.where(y == cls)[0])
        folds[idx] = np.arange(len(idx)) % k
    losses = {}
    for l2 in grid:
        ll = 0.0
        for f in range(k):
            tr, te = folds != f, folds == f
            w = fit_logistic(X[tr], y[tr], l2=l2)
            pt = np.clip(1 / (1 + np.exp(-X[te] @ w)), 1e-6, 1 - 1e-6)
            ll -= float((y[te] * np.log(pt) + (1 - y[te]) * np.log(1 - pt)).sum())
        losses[l2] = ll / len(y)
    print("cv log-loss by l2:", {k: round(v, 4) for k, v in losses.items()})
    return min(losses, key=losses.get)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--cost-ratio", type=float, default=5.0, help="cost of a wrong value / cost of a manual check")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--prior-only", action="store_true",
                    help="keep the hand-set prior coefficients (only choose the threshold on calib)")
    a = ap.parse_args()
    rows = [json.loads(l) for l in (a.run / "field_results.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r.get("raw_correct") is not None and r.get("signals")]
    cal = [r for r in rows if r["split"] == "calib"]
    test = [r for r in rows if r["split"] == "test"]
    Xc, yc = _xy(cal)
    Xt, yt = _xy(test)
    prior = np.array([_PRIOR[f] for f in FEATURES])
    l2 = cv_l2(Xc, yc)
    w = fit_logistic(Xc, yc, l2=l2)
    print(f"chosen l2={l2}")
    sig = lambda X, w: 1 / (1 + np.exp(-X @ w))  # noqa: E731
    self_t = Xt[:, 1]
    print(f"calib n={len(yc)} (acc {yc.mean():.3f})   test n={len(yt)} (acc {yt.mean():.3f})")
    print(f"{'':22}{'ECE(test)':>10}{'AUROC(test)':>13}")
    for name, p in (("model self-conf", self_t), ("prior fusion", sig(Xt, prior)), ("fitted fusion", sig(Xt, w))):
        au = auroc(p, yt)
        print(f"{name:22}{ece(p, yt):>10.4f}{au if au is None else round(au, 4):>13}")
    if a.prior_only:
        w = prior
        print("using prior coefficients (--prior-only)")
    t, prec, cov = pick_threshold(sig(Xc, w), yc, a.cost_ratio)
    pt = sig(Xt, w)
    mt = pt >= t
    print(f"threshold {t} (cost ratio {a.cost_ratio}) -> calib precision {prec:.3f} @ coverage {cov:.3f}; "
          f"test precision {yt[mt].mean() if mt.any() else float('nan'):.3f} @ coverage {mt.mean():.3f}")
    print("coef:", {f: round(float(x), 3) for f, x in zip(FEATURES, w)})
    if a.write:
        out = {"version": f"{'prior' if a.prior_only else 'fit'}-{a.run.name}", "fitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "fitted_on": str(a.run.as_posix()), "n_calib": len(yc), "l2": l2, "cost_ratio": a.cost_ratio,
               "abstain_threshold": t, "coef": {f: round(float(x), 4) for f, x in zip(FEATURES, w)},
               "test_metrics": {"ece": round(ece(pt, yt), 4), "auroc": auroc(pt, yt)}}
        CALIBRATION_FILE.write_text(json.dumps(out, indent=1) + "\n")
        print(f"wrote {CALIBRATION_FILE}")


if __name__ == "__main__":
    main()
