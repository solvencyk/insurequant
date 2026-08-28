import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

rows = json.load(open("PL_breakdown.json", encoding="utf-8"))
by_cq = defaultdict(dict)
for r in rows:
    if not isinstance(r["항목번호"], int):
        continue
    by_cq[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]

resids = []
for (code, q), items in by_cq.items():
    if items.get(25) is None or items.get(32) is None:
        continue
    parts = [items.get(k) for k in (26, 27, 28, 29, 30)]
    if any(p is None for p in parts):
        continue
    total = sum(parts) + items[32]
    resid = items[25] - total
    resids.append((abs(resid), code, q, items[25]))

resids.sort()
print(f"n = {len(resids)}")
print("exactly 0.000000:", sum(1 for r, *_ in resids if r == 0.0))
print("<=0.000001:", sum(1 for r, *_ in resids if r <= 1e-6))
print("<=0.01 (1 원):", sum(1 for r, *_ in resids if r <= 0.01))
print("<=1 (백만원):", sum(1 for r, *_ in resids if r <= 1))
print("\ntop 15 largest absolute residuals:")
for r, code, q, base in resids[-15:]:
    rel = r / max(abs(base), 1e-9)
    print(f"  {code} {q}: |resid|={r:.6f} 백만원  base(item25)={base:,.3f}  rel={rel:.4%}")
