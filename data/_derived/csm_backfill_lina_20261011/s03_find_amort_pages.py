# -*- coding: utf-8 -*-
"""Step 3: pages of every KR0074 PDF that contain the expected-amortisation caption (기대상각기간별 보험계약마진),
with the first 120 normalised chars after the caption, so issued-contract vs reinsurance-held tables are told apart."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

FY = ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4",
      "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4", "FY2026_Q1", "FY2026_Q2"]


def norm(s: str) -> str:
    return re.sub(r"[\s　]+", "", s)


res = {}
for fy in FY:
    f = sorted((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0074_*.pdf"))[0]
    doc = fitz.open(f)
    rows = []
    for i in range(doc.page_count):
        n = norm(doc[i].get_text())
        for m in re.finditer(r"기대상각기간별", n):
            pre = n[max(0, m.start() - 40): m.start()]
            rows.append({"page": i + 1, "pre": pre, "post": n[m.end(): m.end() + 60]})
    res[fy] = rows
    print(fy, f.name)
    for r in rows:
        print("   p", r["page"], "|", r["pre"], "<<기대상각기간별>>", r["post"])
(OUT / "s03_find_amort_pages.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
