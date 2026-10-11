# -*- coding: utf-8 -*-
"""Read-only peek 2: quarterly convention (값 vs 값_당분기) for a company with all four quarters; reinsurer sidecar cells; amort viz."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
codes = sorted({r["원보험사코드"] for r in wf})
print("companies", len(codes))

# a company with 2024.1Q..2024.4Q
for code in ["KR0001", "KR0003", "KR0005"]:
    rows = [r for r in wf if r["원보험사코드"] == code and r["공시분기"].startswith("2024")]
    print("==", code, len(rows))
    for r in sorted(rows, key=lambda r: (r["공시분기"], r["항목번호"])):
        print(r["공시분기"], r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"))

pv = json.loads((ROOT / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))
for c in pv["cells"]:
    if c.get("company_code", "").startswith("KR11") or c.get("source_id") != "DART":
        print(c)
