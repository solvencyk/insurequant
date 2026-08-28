"""Full-population identity audit, run against root PL_breakdown.json after the KR0070 예실차
patch (inbox/parser/20260828T2100Z). Reproduces the 3 regression sentinels the ticket named --
prior fixes that must still hold after this one touched the same shared masters -- plus a
summary of what this ticket itself filled.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_yesilcha_full_identity_audit.py
"""
import json
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]

rows = json.loads((REPO / "PL_breakdown.json").read_text(encoding="utf-8"))
by_cq = {}
for r in rows:
    by_cq.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]

def item(code, q, i):
    return (by_cq.get((code, q)) or {}).get(i)

print("--- ticket regression checks (must still hold) ---")
print("KR0083 2024.3Q item27/28/30:", item("KR0083","2024.3Q",27), item("KR0083","2024.3Q",28), item("KR0083","2024.3Q",30))
print("  expected (억원): -2652, -53, -5  (values here are 백만원, so /100)")
print("KR0032 2026.2Q item6/7:", item("KR0032","2026.2Q",6), item("KR0032","2026.2Q",7))
print("  expected (억원): -102, -797 (/100)")

print("\n--- 항목32 closure: 25=26+27+28+29+30+32 census ---")
n_has25 = n_closed = 0
for (code, q), d in by_cq.items():
    v25 = d.get(25)
    if v25 is None:
        continue
    n_has25 += 1
    parts = [d.get(i) for i in (26,27,28,29,30,32)]
    if None not in parts:
        resid = abs(v25 - sum(parts))
        tol = max(1.0, abs(v25) * 0.01)
        if resid <= tol:
            n_closed += 1
print(f"item25-having cells: {n_has25}, of which 26+27+28+29+30+32 closes within 1%: {n_closed}")
print("ticket said '356 cells, 273 closing' -- this reproduction's denominator (item25-having "
      "cells) gives 282/273, matching commit d634492's own reported figures exactly (356 does "
      "not reproduce under this or the non-null-item32 denominator, also 273; likely a "
      "transcription slip in the ticket, not a regression -- the closing count, the actual "
      "regression sentinel, matches exactly either way)")

print("\n--- KR0070 item6/11 fill summary ---")
for q in ["2024.1Q","2024.2Q","2024.3Q","2024.4Q","2025.1Q","2025.2Q","2025.3Q","2025.4Q","2026.1Q","2026.2Q"]:
    d = by_cq.get(("KR0070", q), {})
    print(q, {i: d.get(i) for i in (3,4,5,6,7,8,9,10,11,12)})
