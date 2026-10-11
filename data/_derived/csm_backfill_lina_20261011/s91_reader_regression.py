# -*- coding: utf-8 -*-
"""Step 91 (read-only): the x-coordinate reader (scripts/_lina_csm_tables_20261011.py) vs the first reader on the 21 pages that were already
proven (core extraction), then the reader on every page of the extension (8 quarters + their comparatives)."""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import _lina_csm_tables_20261011 as R  # noqa: E402
import extract_lina_csm_rows_20261011 as E  # noqa: E402  (the first reader; importing has no side effect)
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)


def doc_of(fy):
    return fitz.open(latest_disclosure_pdfs(fy, "KR0074")[0])


# ---- 1. agreement on the already proven pages
core_pages = []
for q, spec in E.PLAN.items():
    for key in ("cur", "con_cur", "prior"):
        for acct, p in spec[key].items():
            core_pages.append((spec["fy"], p))
for q, spec in E.REGRESSION.items():
    for acct, p in spec["pages"].items():
        core_pages.append((spec["fy"], p))
for q, spec in E.REGRESSION_PRIOR.items():
    for acct, p in spec["pages"].items():
        core_pages.append((spec["fy"], p))
core_pages = sorted(set(core_pages))
agree = 0
for fy, p in core_pages:
    d = doc_of(fy)
    old = E.csm_items(E.read_rollforward(d[p - 1])["rows"])
    rd = R.read_note(d[p - 1])
    prob = R.check_note(rd)
    new = R.csm_items(rd) if not prob else None
    ok = (new == old) and not prob
    agree += ok
    if not ok:
        print("DISAGREE", fy, p, prob, old, new)
print(f"core pages {len(core_pages)}: new reader == first reader and clean on {agree}")

# ---- 2. the extension pages
EXT = [("FY2025_Q1", 57), ("FY2025_Q1", 58), ("FY2025_Q2", 83), ("FY2025_Q2", 84),
       ("FY2024_Q1", 51), ("FY2024_Q1", 52), ("FY2024_Q2", 76), ("FY2024_Q2", 77), ("FY2024_Q3", 52), ("FY2024_Q3", 53),
       ("FY2023_Q1", 57), ("FY2023_Q1", 58), ("FY2023_Q2", 84), ("FY2023_Q2", 85), ("FY2023_Q3", 62), ("FY2023_Q3", 63),
       ("FY2026_Q1", 67), ("FY2026_Q1", 69), ("FY2026_Q2", 92), ("FY2026_Q2", 94),
       ("FY2025_Q3", 64)]
for fy, p in EXT:
    d = doc_of(fy)
    t = R.norm(d[p - 1].get_text())
    per = next((m.strip("<>") for m in ("<당반기>", "<전반기>", "<당분기>", "<전분기>", "<당기>", "<전기>") if m in t), None)
    rd = R.read_note(d[p - 1])
    prob = R.check_note(rd)
    note = ""
    if prob:
        prob1 = R.check_note(rd, csm_tol=1)
        if not prob1:
            note = " [clean only with csm_tol=1: printed 1천원 rounding residual in a CSM column]"
            prob = []
    line = f"{fy} p{p}: period={per} ncols={rd['ncols']} rows={len(rd['rows'])} problems={prob}{note}"
    if not prob:
        it = R.csm_items(rd)
        line += (f"\n      CSM(억원): open {it['open'] / 1e5:.5f} new {it['new'] / 1e5:.5f} fin {it['fin'] / 1e5:.5f} adj {it['adj'] / 1e5:.5f} "
                 f"amort {it['amort'] / 1e5:.5f} close {it['close'] / 1e5:.5f} | combined residual {R.csm_residual(it)} 천원")
    print(line)
