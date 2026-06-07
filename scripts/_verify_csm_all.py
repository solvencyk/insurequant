# -*- coding: utf-8 -*-
"""Full CSM verification after the 2024-life fix:
  (1) 2025.4Q 6 golds, (2) 2024.4Q 한화생명/삼성생명 golds (별도),
  (3) coverage by company×quarter, (4) continuity sanity:
       within-year 기초(opening) constant (YTD), year-boundary 기말[Q4,N]≈기초[Q1,N+1]."""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

DIAG = ROOT / "data/dart/viz/csm_waterfall_master_diag.json"
rows = json.loads(DIAG.read_text(encoding="utf-8"))

# index: (name, quarter) -> {item_no: value}
by = defaultdict(dict)
names = {}
for r in rows:
    by[(r["원수사명"], r["공시분기"])][r["항목번호"]] = r["값"]
    names[r["원수사명"]] = r["생손보여부"]

GOLD_2025 = {  # 기초 CSM (item 1), 억
    "메리츠화재": 111878.9, "KB손해보험": 88204.8, "삼성화재": 140739.1,
    "한화손해보험": 38032.2, "한화생명": 91091.4, "삼성생명": 129020.2}
GOLD_2024 = {"한화생명": 92384.88, "삼성생명": 122473.72}  # 별도 기초, 억

def find_name(part):
    for n in names:
        if part in n:
            return n
    return None

print("=== 2025.4Q 6 golds (기초) ===")
for part, g in GOLD_2025.items():
    n = find_name(part) or part
    v = by.get((n, "2025.4Q"), {}).get(1)
    ok = v is not None and abs(v - g) <= max(1.0, abs(g) * 0.002)
    print(f"  {part:10s} {str(v):>12} (g{g}) {'OK' if ok else 'XX'}")

print("\n=== 2024.4Q life golds (별도 기초) ===")
for part, g in GOLD_2024.items():
    n = find_name(part) or part
    d = by.get((n, "2024.4Q"), {})
    v = d.get(1)
    ok = v is not None and abs(v - g) <= max(1.0, abs(g) * 0.002)
    print(f"  {part:10s} 기초={str(v):>12} (g{g}) {'OK' if ok else 'XX'}  "
          f"신계약={d.get(2)} 이자={d.get(3)} 상각={d.get(5)} 기말={d.get(6)}")

# continuity
print("\n=== continuity sanity (flag suspicious) ===")
companies = sorted({n for n, _q in by})
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)]
flagged = []
for n in companies:
    series = {q: by[(n, q)].get(1) for q in QS if (n, q) in by}
    closes = {q: by[(n, q)].get(6) for q in QS if (n, q) in by}
    # within-year opening constant
    yr_open = defaultdict(dict)
    for q, v in series.items():
        if v is not None:
            yr_open[q[:4]][q] = v
    for yr, om in yr_open.items():
        vals = list(om.values())
        if len(vals) >= 2:
            lo, hi = min(vals), max(vals)
            if hi and abs(hi - lo) / max(abs(hi), 1) > 0.02:
                flagged.append(f"{n} {yr}: 기초 not constant within year {om}")
    # year-boundary 기말[Q4,N] ~ 기초[Q1,N+1]
    for y in (2023, 2024, 2025):
        c4 = closes.get(f"{y}.4Q"); o1 = series.get(f"{y+1}.1Q")
        if c4 is not None and o1 is not None and max(abs(c4), abs(o1)) > 1:
            if abs(c4 - o1) / max(abs(c4), abs(o1)) > 0.03:
                flagged.append(f"{n} {y}.4Q기말={c4} vs {y+1}.1Q기초={o1} mismatch")
if flagged:
    for f in flagged:
        print("  FLAG", f)
else:
    print("  (no continuity flags)")

# coverage count per quarter
print("\n=== coverage: companies with non-null 기초 per quarter ===")
for q in QS:
    cnt = sum(1 for n in companies if by.get((n, q), {}).get(1) is not None)
    if cnt:
        print(f"  {q}: {cnt} companies")
print(f"\ntotal companies seen: {len(companies)}")
