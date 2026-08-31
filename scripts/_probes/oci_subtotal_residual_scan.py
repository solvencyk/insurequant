import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

d = json.load(open("PL_breakdown.json", encoding="utf-8"))

# group by (company_code, quarter) -> {item_no: value}
by_cq = defaultdict(dict)
name_by_code = {}
for r in d:
    key = (r["원보험사코드"], r["공시분기"])
    by_cq[key][r["항목번호"]] = r["값"]
    name_by_code[r["원보험사코드"]] = r["원수사명"]

rows = []
for (code, q), items in by_cq.items():
    if 25 not in items:
        continue
    comps = [items.get(i) for i in (26, 27, 28, 29, 30)]
    if any(c is None for c in comps):
        continue  # not comparable — matches ticket's "273 비교가능 셀"
    subtotal = items[25]
    comp_sum = sum(comps)
    residual = subtotal - comp_sum
    denom = max(abs(subtotal), abs(comp_sum), 1e-9)
    rel = abs(residual) / denom
    rows.append((code, name_by_code[code], q, subtotal, comp_sum, residual, rel, comps))

rows.sort(key=lambda x: -x[6])

n_total = len(rows)
n_gt1pct = sum(1 for r in rows if r[6] > 0.01)
n_gt10pct = sum(1 for r in rows if r[6] > 0.10)
print(f"comparable cells: {n_total}")
print(f"residual > 1%: {n_gt1pct}")
print(f"residual > 10%: {n_gt10pct}")

print("\n=== top 15 by relative residual ===")
for code, name, q, subtotal, comp_sum, residual, rel, comps in rows[:15]:
    print(f"{name}({code}) {q}: item25(소계)={subtotal:,.1f}  sum(26-30)={comp_sum:,.1f}  residual={residual:,.1f}  rel={rel:.1%}")
    print(f"    comps 26-30 = {[round(c,1) for c in comps]}")
