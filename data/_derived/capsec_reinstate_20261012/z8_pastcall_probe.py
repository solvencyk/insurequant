# -*- coding: utf-8 -*-
"""Pre-2023 ledger bonds with past_call_outstanding=true (outstanding but past first call date) - read only."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")
doc = json.loads((ROOT / "data/bonds/capital_securities_fy2026h1.json").read_text(encoding="utf-8"))
n = 0
for c in doc["companies"]:
    for b in c["bonds"]:
        if b.get("past_call_outstanding") and (b.get("outstanding_mn") or 0) > 0:
            n += 1
            pre = (b.get("issue_date") or "") < "2023-01-01"
            print(f"{c['code']} {c['company'][:8]:8s} {b['tier']:12s} issue {b.get('issue_date')} call {b.get('call_date')} out {b['outstanding_mn']/100:9.1f}억 "
                  f"pre2023={pre} as_of {b.get('as_of')} | {b['name'][:40]}")
print("count", n)
