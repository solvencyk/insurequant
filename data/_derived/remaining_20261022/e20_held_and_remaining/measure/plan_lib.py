# -*- coding: utf-8 -*-
"""plan_lib: shared helpers for the candidate cell lists (READ-ONLY).
closure(v)           strict identity residuals of a candidate PL vector (mn)
changed(code,q,v)    [(item, old, new)] against the live-master snapshot (owner-gold cells included, flagged by the caller)
cite_statement(...)  find the printed cell (label, line) of a Tier-1 value in the LATER filing's separate statement (prior YTD column)
screen(...)          headline movement in 억원
"""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402
import stmtlib as S  # noqa: E402

TOL = 0.0015  # mn: identity tolerance for exact (원-precise) vectors


def closure(v: dict, nonlife: bool = False) -> dict:
    """identity residuals (candidate - 0).  None when an input is missing."""
    def g(i):
        return v.get(i)
    def res(expr_ok, f):
        return f() if expr_ok else None
    out = {}
    out["I1 20=1+17"] = res(None not in (g(20), g(1), g(17)), lambda: g(1) + g(17) - g(20))
    out["I2 22=20+21"] = res(None not in (g(22), g(20), g(21)), lambda: g(20) + g(21) - g(22))
    out["I3 24=22-23"] = res(None not in (g(24), g(22), g(23)), lambda: g(22) - g(23) - g(24))
    out["I4 31=24+25"] = res(None not in (g(31), g(24), g(25)), lambda: g(24) + g(25) - g(31))
    out["I5 25=26..30+32"] = res(all(g(k) is not None for k in (25, 26, 27, 28, 29, 30, 32)),
                                 lambda: sum(g(k) for k in (26, 27, 28, 29, 30, 32)) - g(25))
    out["I6 17=18+19"] = res(None not in (g(17), g(18), g(19)), lambda: g(18) + g(19) - g(17))
    if g(1) is not None and g(2) is not None:
        legs = g(2) + (0.0 if not nonlife else (g(13) or 0.0) + (g(14) or 0.0))
        bare = legs - g(1)
        adj = legs + (g(15) or 0.0) - (g(16) or 0.0) - g(1)
        out["I7 LOB bridge (min of bare/adj)"] = min((bare, adj), key=abs)
    else:
        out["I7 LOB bridge (min of bare/adj)"] = None
    return out


def changed(code: str, q: str, v: dict, master_pl: dict, items=range(1, 33)):
    m = master_pl.get((code, q), {})
    out = []
    for it in items:
        new, old = v.get(it), m.get(it)
        if new is None and old is None:
            continue
        if new is None:          # never blank a published cell
            continue
        if old is None or abs(new - old) > 1e-6:
            out.append((it, old, new))
    return out


def screen_eok(code: str, q: str, v: dict, master_pl: dict):
    """headline movement in 억원 (백만원/100) for 보험손익(1) / 투자손익(17) / 당기순이익(24) + OCI(25)"""
    m = master_pl.get((code, q), {})
    out = {}
    for it, nm in ((1, "보험손익"), (17, "투자손익"), (24, "당기순이익"), (25, "기타포괄손익"), (31, "총포괄손익")):
        a, b = m.get(it), v.get(it)
        if a is not None and b is not None and abs(a - b) > 1e-6:
            out[nm] = (round(a / 100, 2), round(b / 100, 2), round((b - a) / 100, 2))
    return out


def unit_of(lines, table) -> float:
    """to 백만원 divisor for a table: reads '(단위 : 원|천원|백만원|억원)' in the 12 lines before the table and the first rows"""
    blob = " ".join(lines[max(0, table["start"] - 14): table["start"]])
    blob += " " + " ".join(c["text"] for r in table["rows"][:2] for c in r["cells"])
    m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원|억원|만원)", blob)
    u = m.group(1) if m else "원"
    return {"원": 1e6, "천원": 1e3, "백만원": 1.0, "억원": 0.01, "만원": 100.0}[u]


def cite_statement(lines, table, target_mn: float, prefer_last=True, tol=6e-7):
    """cells of the statement table whose value (converted to 백만원) equals |target| (sign ignored: presentation) -> [(label, line, text, tr_line)]"""
    div = unit_of(lines, table)
    out = []
    for r in table["rows"]:
        if not r["cells"]:
            continue
        label = r["cells"][0]["text"]
        cells = r["cells"][1:]
        for k, c in enumerate(cells):
            if c["val"] is None:
                continue
            mn = abs(c["val"]) / div
            if abs(mn - abs(target_mn)) <= max(tol, abs(target_mn) * 2e-9):
                out.append((label, c["line"], c["text"], r["tr_line"], k, len(cells)))
    return out
