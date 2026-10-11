# -*- coding: utf-8 -*-
"""Read-only cross-check: Lina closing CSM per quarter in CSM_waterfall.json (new rows) vs insurance_liability_portfolio.json
(2-4 보험부채 현황 CSM items). Prints every KR0074 ILP row of the quarters of interest so the item semantics are visible."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
print("ILP rows", len(ilp), "keys", list(ilp[0].keys()))
rows = [r for r in ilp if r.get("원보험사코드") == "KR0074"]
print("KR0074 rows", len(rows))
qs = ["2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]
names = {}
for r in rows:
    names[r.get("항목번호")] = r.get("항목명")
print("item names:", names)
for q in qs:
    sel = sorted([r for r in rows if r["공시분기"] == q], key=lambda r: r["항목번호"])
    print("==", q)
    for r in sel:
        if r["항목번호"] in (1, 2, 3, 4, 5, 6, 7, 8, 9):
            print("  ", r["항목번호"], r["항목명"], r.get("값"), {k: v for k, v in r.items() if k not in ("원보험사코드", "원수사명", "티커", "생손보여부", "항목번호", "항목명", "공시분기", "값")})
wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
print("waterfall closes:", {r["공시분기"]: r["값"] for r in wf if r["원보험사코드"] == "KR0074" and r["항목번호"] == 6})
