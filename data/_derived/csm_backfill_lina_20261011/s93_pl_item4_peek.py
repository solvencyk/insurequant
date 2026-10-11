# -*- coding: utf-8 -*-
"""Step 93 (read-only): KR0074 PL_breakdown item 4 (원수 CSM상각) per quarter right now (another agent is writing PL_breakdown.json)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
rows = [r for r in pl if r["원보험사코드"] == "KR0074"]
qs = sorted({r["공시분기"] for r in rows})
print("PL rows KR0074:", len(rows), "quarters:", qs)
for q in qs:
    items = {r["항목번호"]: r["값"] for r in rows if r["공시분기"] == q}
    print(q, "item4 =", items.get(4), "| items present:", sorted(k for k, v in items.items() if v is not None))
wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
print("waterfall amort (item 5):", {r["공시분기"]: r["값"] for r in wf if r["원보험사코드"] == "KR0074" and r["항목번호"] == 5})
