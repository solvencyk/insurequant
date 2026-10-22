#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 18: check three claims before they go into the ticket answer (read-only) -> s18_claims_check.txt
 (a) KDB생명 (KR0072) live master I1 residual 20-(1+17) for every quarter (is 2025.4Q already off by the 기타영업손익 split?)
 (b) KR0083 2024.3Q: note-50 second source (before/after) versus the planned old/new for all 8 cells
 (c) which pre-existing builder-drift cell did the apply fix (snapshot drift list minus the drift list now)"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
L = []
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in live}
L.append("(a) KR0072 live master 20-(1+17) per quarter:")
for y in (2023, 2024, 2025, 2026):
    for n in (1, 2, 3, 4):
        q = f"{y}.{n}Q"
        v1, v17, v20 = M.get(("KR0072", 1, q)), M.get(("KR0072", 17, q)), M.get(("KR0072", 20, q))
        if None in (v1, v17, v20):
            continue
        L.append(f"   {q}: 20={v20:.3f} 1={v1:.3f} 17={v17:.3f} resid={v20 - v1 - v17:+.3f}")
plan = json.loads((HERE / "e20_plan.json").read_text(encoding="utf-8"))
L.append("(b) KR0083 2024.3Q note-50 second source:")
for b in plan["buckets"]:
    if b.get("code") == "KR0083" and b.get("quarter") == "2024.3Q":
        for c in b["cells"]:
            s = c.get("second_source_note50")
            L.append(f"   i{c['item']}: old={c['old']} new={c['new']} note50 before={None if not s else s['before']} after={None if not s else s['after']} after_vs_new={None if not s else s['after_vs_new']} before_vs_old={None if not s else s['before_vs_old']}")
L.append("(c) pre-existing drift cells fixed by the apply:")
import e20_apply as A  # noqa: E402  (module import only)
live_rows = A.load_json(A.F["PL"])
gold = A.load_json(A.F["GOLD"])
base = A.simulate_rows(gold, "claims")
now = {tuple(k) for k in A.drift_vs_live(live_rows, base)}
snap = {tuple(x) for x in json.loads((HERE / "pl_drift_before.json").read_text(encoding="utf-8"))["drift_all"]}
L.append(f"   snapshot {len(snap)} now {len(now)}; fixed {sorted(snap - now)}; new {sorted(now - snap)}")
(HERE / "s18_claims_check.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("\n".join(L))
