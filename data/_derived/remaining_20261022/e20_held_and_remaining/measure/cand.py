# -*- coding: utf-8 -*-
"""cand: build the candidate PL vector (items 1..32) of a (company, quarter) for a chosen Tier-1 vintage with the PRODUCTION assemble().
vector(code, q, which)   which = 'same' (the quarter's own filing) | 'prior' (the next-year filing's prior column = latest comparative)
t2 defaults to the live master's note items (4,5,6,9,10,11 [+ for 손보 whatever the caller passes: 13/14/_jang_*/_jang_net]).
READ-ONLY (imports build_pl_breakdown.assemble)."""
from __future__ import annotations

import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import fsapi as F  # noqa: E402  (chdir + sys.path)
import mlib as M  # noqa: E402

import build_pl_breakdown as BP  # noqa: E402

_PL = None


def master():
    global _PL
    if _PL is None:
        _PL = M.load_pl()[0]
    return _PL


def vector(code: str, q: str, which: str = "prior", t2=None, is_life=None, zero_fill_ok=None):
    pl = master()
    m = pl.get((code, q), {})
    t1, _ = (F.prior(code, q) if which == "prior" else F.same(code, q))
    if t1 is None:
        return None, None
    if is_life is None:
        is_life = (m.get(13) == 0.0 and m.get(14) == 0.0)
    if t2 is None:
        t2 = {k: m[k] for k in (4, 5, 6, 9, 10, 11) if m.get(k) is not None}
    v = BP.assemble(dict(t1), dict(t2), is_life, zero_fill_ok=zero_fill_ok)
    return v, t1


def diff_vs_master(code: str, q: str, v: dict, items=range(1, 33)):
    m = master().get((code, q), {})
    out = []
    for it in items:
        new = v.get(it)
        old = m.get(it)
        if new is None and old is None:
            continue
        if new is None or old is None or abs(new - old) > 1e-6:
            out.append((it, old, new))
    return out
