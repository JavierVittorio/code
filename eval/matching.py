"""Field and line-item comparison. Uses the same normalizers as extraction (docext.normalize) so the
metric measures *reading* errors, not formatting differences.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
from rapidfuzz import fuzz
from rapidfuzz.distance import OSA
from scipy.optimize import linear_sum_assignment

from docext.normalize import (norm_ident, norm_text, parse_currency, parse_date, parse_doctype, parse_money,
                              parse_number, parse_rate)
from docext.schema import FIELD_SPECS, Kind

TEXT_MATCH = 90  # token_sort_ratio threshold for names/addresses to count as correct
TEXT_NEAR = 70


@dataclass
class Match:
    correct: bool
    near_miss: bool = False  # wrong, but close: OCR char confusion, 1-char ident diff, small text diff
    detail: str = ""


def _money(v):
    m = parse_money(v)
    return None if m is None else abs(m)


def compare_value(name: str, pred, gt, alts: list | None = None) -> Match:
    kind = FIELD_SPECS[name][0]
    for g in [gt, *(alts or [])]:
        m = _compare(kind, pred, g)
        if m.correct:
            return m
    return _compare(kind, pred, gt)


def _compare(kind: Kind, pred, gt) -> Match:
    if kind in (Kind.money,):
        p, g = _money(pred), _money(gt)
        if p is None:
            return Match(False, detail="unparseable")
        if p == g:
            return Match(True)
        # near miss: adjacent digit transposition / single digit OCR error / 1 cent rounding
        near = abs(p - g) <= Decimal("0.01") or OSA.distance(str(p), str(g)) == 1
        return Match(False, near, f"{p} vs {g}")
    if kind == Kind.rate:
        p, g = parse_rate(pred), parse_rate(gt)
        return Match(p is not None and g is not None and p == g, detail=f"{p} vs {g}")
    if kind == Kind.date:
        p, g = parse_date(pred), parse_date(gt)
        if p == g and p is not None:
            return Match(True)
        swapped = p is not None and g is not None and p.day == g.month and p.month == g.day and p.year == g.year
        return Match(False, swapped, "day/month swapped" if swapped else f"{p} vs {g}")
    if kind == Kind.ident:
        p, g = norm_ident(pred), norm_ident(gt)
        if p == g and p:
            return Match(True)
        return Match(False, OSA.distance(p, g) <= 1, f"{pred!r} vs {gt!r}")
    if kind == Kind.currency:
        return Match(parse_currency(pred) == parse_currency(gt) is not None)
    if kind == Kind.doctype:
        return Match(parse_doctype(pred) == parse_doctype(gt) is not None)
    s = fuzz.token_sort_ratio(norm_text(pred), norm_text(gt))
    return Match(s >= TEXT_MATCH, TEXT_NEAR <= s < TEXT_MATCH, f"sim={s:.0f}")


# ------------------------------------------------------------------ line items
@dataclass
class ItemScore:
    n_gt: int
    n_pred: int
    matched: int  # pairs aligned by Hungarian assignment
    exact_rows: int  # matched pairs with every labeled cell correct
    cells_correct: dict[str, int]
    cells_total: dict[str, int]


def _desc_sim(p, g) -> float:
    """Descriptions often carry article codes on one side only ('202BR7224T1401XS JERSEY DE PUNTO' vs
    'JERSEY DE PUNTO'): accept a full-token subset match once the shorter side is non-trivial."""
    a, b = norm_text(p), norm_text(g)
    s = fuzz.token_sort_ratio(a, b)
    if min(len(a), len(b)) >= 8:
        s = max(s, fuzz.token_set_ratio(a, b))
    return s


def _cell_ok(cell: str, p, g, alts=None) -> bool:
    if cell == "description":
        return _desc_sim(p, g) >= 80
    if cell == "quantity":
        a, b = parse_number(p), parse_number(g)
        return a is not None and b is not None and a == b
    a = _money(p)
    return a is not None and any(a == _money(x) for x in [g, *(alts or [])])


def score_line_items(pred: list[dict], gt: list[dict], cells: list[str]) -> ItemScore:
    """Optimal 1:1 alignment (Hungarian) on description similarity + amount agreement, then cell scoring.
    Order-independent, robust to a dropped/duplicated row (which shifts naive positional matching)."""
    n, m = len(gt), len(pred)
    cc = {c: 0 for c in cells}
    ct = {c: 0 for c in cells}
    if n == 0 or m == 0:
        return ItemScore(n, m, 0, 0, cc, {c: sum(1 for g in gt if g.get(c) is not None) for c in cells})
    sim = np.zeros((n, m))
    for i, g in enumerate(gt):
        for j, p in enumerate(pred):
            s = _desc_sim(p.get("description"), g.get("description")) / 100
            # agreement on the other labeled cells + row-order proximity break ties between repeated
            # descriptions (otherwise identical "Freight" rows get cross-matched and score as cell errors)
            for c in cells:
                if c != "description" and g.get(c) is not None:
                    s += 0.3 * _cell_ok(c, p.get(c), g.get(c), g.get("alt_amounts") if c == "amount" else None)
            s += 0.2 * (1 - abs(i / max(n - 1, 1) - j / max(m - 1, 1)))
            sim[i, j] = s
    rows, cols = linear_sum_assignment(-sim)
    matched = exact = 0
    for i, j in zip(rows, cols):
        if sim[i, j] < 0.7:  # too dissimilar to be the same row: count as unmatched
            continue
        matched += 1
        ok_all = True
        for c in cells:
            if gt[i].get(c) is None:  # cell not printed on the document: nothing to score
                continue
            ok = _cell_ok(c, pred[j].get(c), gt[i].get(c), gt[i].get("alt_amounts") if c == "amount" else None)
            cc[c] += ok
            ok_all &= ok
        exact += ok_all
    for c in cells:
        ct[c] = sum(1 for g in gt if g.get(c) is not None)
    return ItemScore(n, m, matched, exact, cc, ct)
