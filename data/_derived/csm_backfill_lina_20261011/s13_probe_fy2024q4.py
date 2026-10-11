# -*- coding: utf-8 -*-
"""Step 13 (read-only probe): layout of the CSM roll-forward pages in the FY2024_Q4 / FY2023_Q4 / FY2025_Q1 / FY2025_Q2 PDFs
(only to extend the regression against the existing year-end master rows and to census the other quarters)."""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lina_tbl as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

PROBE = {
    "FY2024_Q4": [212, 213, 223, 224],
    "FY2023_Q4": [142, 143, 147, 148],
    "FY2025_Q1": [57, 58, 64, 65],
    "FY2025_Q2": [83, 84, 90, 91],
}
for fy, pages in PROBE.items():
    pdf = sorted((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0074_*.pdf"))[0]
    doc = fitz.open(pdf)
    print(f"\n== {fy} {pdf.name}")
    for p in pages:
        pg = doc[p - 1]
        t = T.norm(pg.get_text())
        acct = "유배당외" if "유배당외보험" in t else ("유배당" if "유배당보험" in t else None)
        per = next((m.strip("<>") for m in ("<당반기>", "<전반기>", "<당분기>", "<전분기>", "<당기>", "<전기>") if m in t), None)
        rf = T.read_rollforward(pg)
        probs = T.check_rollforward(rf["rows"]) if not rf["bad"] else ["bad rows"]
        line = f"  p{p}: acct={acct} period={per} rows={len(rf['rows'])} dup={rf['duplicates']} problems={probs}"
        if not probs:
            it = T.csm_items(rf["rows"])
            line += f"\n      CSM(천원) {({k: v for k, v in it.items() if k != 'total_col'})}"
        print(line)
