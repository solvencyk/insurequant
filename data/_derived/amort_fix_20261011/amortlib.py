# -*- coding: utf-8 -*-
"""Shared helpers for the a0x probes (ticket 20261011T1900Z): replay of the panel builder's candidate selection.

`eligible` is a verbatim copy of the nested `_eligible` in viz_build_ifrs17_panels.extract_amort_schedule -- a04 asserts that the
builder (after the fix) still produces the same candidate list, so a drift between this copy and the builder is caught.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(W))

import viz_build_ifrs17_panels as V  # noqa: E402

KW = ("상각", "인식", "예상", "기대", "CSM")


def eligible(b: dict) -> bool:
    if not any(k in str(b.get("caption") or "") for k in KW):
        return False
    if V.header_has_year_buckets(b.get("header") or []):
        return True
    rows = b.get("rows") or []
    for k in range(min(3, len(rows))):
        if V._row_has_year_buckets(rows[k]):
            return True
    stubs = [str(r[0]).strip() for r in rows[:6] if r]
    return sum(1 for s in stubs if V._classify_bucket_cell(s) is not None) >= 3


def iter_files():
    """(company, rcept, path, blocks) for every extracted *_csm.json that has a 14-digit rcept"""
    for p in sorted(V.SRC.glob("*_csm.json")):
        m = V._FILENAME_RE.match(p.stem)
        if not m:
            continue
        blocks = json.loads(p.read_text(encoding="utf-8"))
        yield m.group(1), m.group(2), p, (blocks if isinstance(blocks, list) else [blocks])
