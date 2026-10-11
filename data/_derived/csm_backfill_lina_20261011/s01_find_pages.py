# -*- coding: utf-8 -*-
"""Step 1: find, in every KR0074 management-disclosure PDF, the pages that carry the CSM roll-forward note,
the expected-amortization schedule and other CSM prose. Read-only. Independent of the survey scripts."""
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

KEYS = {
    "rollforward": ["기초잔액", "최초인식한계약의효과", "기말잔액"],            # measurement-component roll-forward table
    "csm_adj": ["보험계약마진조정하는추정치의변동분"],
    "csm_amort": ["제공한서비스반영인식한보험계약마진"],
    "expected_amort": ["보험계약마진", "1년이하", "1년초과"],                  # amortisation schedule (loose)
    "amort_sched2": ["기대", "상각"],
}


def norm(s: str) -> str:
    return re.sub(r"[\s　]+", "", s)


res = {}
for fy in FY:
    pdfs = sorted((ROOT / "data" / "disclosure" / fy / "raw").glob("KR0074_*.pdf"))
    if not pdfs:
        res[fy] = {"error": "no pdf"}
        continue
    f = pdfs[0]
    doc = fitz.open(f)
    hits = {"file": str(f.relative_to(ROOT)).replace("\\", "/"), "pages": doc.page_count, "rollforward": [], "csm_adj": [], "csm_amort": [], "exp_amort": []}
    textpages = 0
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if len(t.strip()) > 80:
            textpages += 1
        n = norm(t)
        if all(k in n for k in KEYS["rollforward"]) and "보험계약마진" in n:
            hits["rollforward"].append(i + 1)
        if all(k in n for k in KEYS["csm_adj"]):
            hits["csm_adj"].append(i + 1)
        if all(k in n for k in KEYS["csm_amort"]):
            hits["csm_amort"].append(i + 1)
        if "보험계약마진" in n and ("1년이하" in n or "1년이내" in n) and ("5년초과" in n or "10년초과" in n or "10년" in n) and ("기대" in n or "상각" in n or "인식" in n):
            hits["exp_amort"].append(i + 1)
    hits["text_pages"] = textpages
    res[fy] = hits
    print(fy, f.name, "pages", doc.page_count, "textpages", textpages, "rollfwd", hits["rollforward"], "adj", hits["csm_adj"],
          "amort", hits["csm_amort"], "expamort", hits["exp_amort"])
(OUT / "s01_find_pages.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
