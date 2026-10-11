# -*- coding: utf-8 -*-
"""Step 10: read the CSM roll-forward pages of the target quarters (+ the 2025.4Q regression quarter) and run every check.

Prints, per page: markers (account / period), problems (empty = clean), the six CSM items in 천원.
Writes s10_read_tables.json (raw numbers per page) for the later steps.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lina_tbl as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

# (quarter, FY dir, pages (separate-entity set, 별도), pages of the consolidated set (연결) for the equality check)
PLAN = {
    "2026.2Q": ("FY2026_Q2", [91, 92, 93, 94], [161, 162, 163, 164]),
    "2026.1Q": ("FY2026_Q1", [66, 67, 68, 69], [137, 138, 139, 140]),
    "2025.3Q": ("FY2025_Q3", [63, 64], [130, 131]),
    "2025.4Q": ("FY2025_Q4", [232, 233, 234, 235], [361, 362, 363, 364]),
}


def markers(page):
    t = T.norm(page.get_text())
    acct = "유배당외" if "유배당외보험" in t else ("유배당" if "유배당보험" in t else None)
    per = None
    for m in ("<당반기>", "<전반기>", "<당분기>", "<전분기>", "<당기>", "<전기>"):
        if m in t:
            per = m.strip("<>")
            break
    basis = "연결" if ("연결실체" in t) else ("별도" if "회사가" in t or "회사는" in t else None)
    caption = ("측정요소별변동내역" in t)
    return acct, per, basis, caption


res = {}
for q, (fy, sep_pages, con_pages) in PLAN.items():
    pdf = sorted((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0074_*.pdf"))[0]
    doc = fitz.open(pdf)
    print(f"\n===== {q}  {pdf.relative_to(ROOT)} =====")
    res[q] = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "pages": {}}
    for label, pages in (("sep", sep_pages), ("con", con_pages)):
        for p in pages:
            pg = doc[p - 1]
            acct, per, basis, caption = markers(pg)
            rf = T.read_rollforward(pg)
            probs = T.check_rollforward(rf["rows"]) if not rf["bad"] else ["bad rows: %s" % rf["bad"]]
            if rf["duplicates"]:
                probs.append(f"duplicate labels {rf['duplicates']}")
            print(f"  {label} p{p}: acct={acct} period={per} basis={basis} caption_on_page={caption} rows={len(rf['rows'])} problems={probs}")
            entry = {"account": acct, "period": per, "rows": rf["rows"], "problems": probs, "set": label}
            if not probs:
                it = T.csm_items(rf["rows"])
                entry["csm"] = it
                print("      CSM(천원):", {k: v for k, v in it.items() if k != 'total_col'}, "| total-col open/close", it["total_col"])
            res[q]["pages"][f"{label}_p{p}"] = entry
(OUT / "s10_read_tables.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
