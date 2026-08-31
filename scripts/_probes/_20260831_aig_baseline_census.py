# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

print(f"TOTAL_ROWS={len(data)}")
combos = set()
for r in data:
    combos.add((r.get("원보험사코드"), r.get("공시분기")))
print(f"TOTAL_COMBOS={len(combos)}")

aig_rows = [r for r in data if r.get("원보험사코드") == "KR0029"]
print(f"KR0029_ROWS={len(aig_rows)}")
aig_quarters = {}
for r in aig_rows:
    q = r.get("공시분기")
    aig_quarters.setdefault(q, 0)
    aig_quarters[q] += 1
for q in sorted(aig_quarters):
    print(f"KR0029 {q}: {aig_quarters[q]} rows")

# distinct quarters overall, and companies per quarter (for coverage cross-check)
quarters = sorted({q for (_, q) in combos})
print(f"ALL_QUARTERS ({len(quarters)}): {quarters}")

# companies count per quarter near AIG's target quarters
targets = ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q","2025.1Q","2025.2Q","2025.3Q"]
for t in targets:
    n = sum(1 for (c,q) in combos if q == t)
    print(f"{t}: {n} companies total (incl AIG? {'KR0029' in [c for (c,q) in combos if q==t]})")
