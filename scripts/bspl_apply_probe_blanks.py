#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""List the BLANK / DIFF item states of the follow-up DART summary-BS probe (data/_derived/bspl_followup_20261011/dart_summary_bs_probe.json) and re-check
each BLANK against the CURRENT master (it may have been filled meanwhile).  Read-only."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
probe = json.loads((ROOT / "data/_derived/bspl_followup_20261011/dart_summary_bs_probe.json").read_text(encoding="utf-8"))
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
blank, diff = [], []
for p in probe:
    for t in p.get("tied", []):
        for it, st in t.get("items", {}).items():
            if st["state"] == "BLANK":
                blank.append((p["code"], int(it), p["quarter"], st["dart"], t["line"], p["xml"], mv.get((p["code"], int(it), p["quarter"]))))
            elif st["state"] not in ("EQUAL",):
                diff.append((p["code"], int(it), p["quarter"], st))
print(f"BLANK states: {len(blank)}")
for b in blank:
    print("  ", b)
print(f"other states: {len(diff)}")
for d in diff[:20]:
    print("  ", json.dumps(d, ensure_ascii=False)[:260])
