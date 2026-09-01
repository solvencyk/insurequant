"""Non-null value census: a master row with 값=null is NOT coverage.

Prints per (company, quarter) how many of the 24 core items actually carry a value.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

recs = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
QUARTERS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)]
QUARTERS = [q for q in QUARTERS if "2023.1Q" <= q <= "2026.2Q"]

core = collections.defaultdict(int)   # (code,q) -> non-null among items 1..24
allrows = collections.defaultdict(int)
names = {}
for r in recs:
    key = (r["원보험사코드"], r["공시분기"])
    names[r["원보험사코드"]] = r["원수사명"]
    allrows[key] += 1
    if isinstance(r["항목번호"], int) and 1 <= r["항목번호"] <= 24 and r["값"] is not None:
        core[key] += 1

print("=== company-quarters present in master but with ZERO non-null core items ===")
empty = sorted(k for k in allrows if core[k] == 0)
for code, q in empty:
    print(f"  {code:7s} {names[code][:22]:22s} {q}  rows={allrows[(code,q)]}  nonnull_core=0")
print(f"  total: {len(empty)}")
print()

print("=== per-company: quarters with >=1 non-null core item ===")
print(f"{'code':7s} {'name':24s} {'nQ_rows':>7s} {'nQ_value':>8s}  min_q_with_value")
codes = sorted({c for c, _ in allrows})
for code in codes:
    qs_rows = sorted({q for c, q in allrows if c == code}, key=QUARTERS.index)
    qs_val = sorted({q for (c, q), n in core.items() if c == code and n > 0}, key=QUARTERS.index)
    if len(qs_val) == len(QUARTERS):
        continue
    print(f"{code:7s} {names[code][:24]:24s} {len(qs_rows):7d} {len(qs_val):8d}  "
          f"{qs_val[0] if qs_val else '-'}")
print()

print("=== AIA (KR0080) full row dump for every quarter present ===")
for r in recs:
    if r["원보험사코드"] == "KR0080":
        print(f"  {r['공시분기']}  item{r['항목번호']:>2} {r['항목명'][:22]:22s} "
              f"값={r['값']}  당분기={r.get('값_당분기')}")
