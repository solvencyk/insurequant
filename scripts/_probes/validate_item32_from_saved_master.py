"""Final validation: read item25-32 directly from the SAVED PL_breakdown.json (not fresh
tier1_for() calls) and check the identity 25 == 26+27+28+29+30+32.  This is what actually
ships -- confirms the surgical patch + build_pl() propagation didn't introduce any drift
from the fetch_dart_fs.py logic validated earlier."""
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

rows = json.load(open("PL_breakdown.json", encoding="utf-8"))
by_cq = defaultdict(dict)
name_by_code = {}
for r in rows:
    if not isinstance(r["항목번호"], int):
        continue
    by_cq[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]
    name_by_code[r["원보험사코드"]] = r["원수사명"]

targets = [(c, q) for (c, q), items in by_cq.items() if items.get(25) is not None]
print(f"cells with item25 non-null: {len(targets)}")

no_item32, reconciled, close, unresolved = [], [], [], []
for code, q in sorted(targets):
    items = by_cq[(code, q)]
    v32 = items.get(32)
    if v32 is None:
        no_item32.append((code, name_by_code[code], q))
        continue
    it25 = items[25]
    total = sum((items.get(k) or 0) for k in (26, 27, 28, 29, 30)) + v32
    resid = it25 - total
    rel = abs(resid) / max(abs(it25), abs(total), 1e-9)
    row = (code, name_by_code[code], q, it25, total, resid, rel)
    if rel <= 0.01:
        reconciled.append(row)
    elif rel <= 0.05:
        close.append(row)
    else:
        unresolved.append(row)

total_n = len(targets)
print(f"item32 absent (documented source gap): {len(no_item32)}")
by_code = defaultdict(int)
for code, name, q in no_item32:
    by_code[(code, name)] += 1
for (code, name), n in sorted(by_code.items(), key=lambda x: -x[1]):
    print(f"   {code} {name}: {n}")

print(f"\nreconciled (<=1%): {len(reconciled)}  ({len(reconciled)/total_n*100:.1f}% of {total_n})")
print(f"close (1-5%):      {len(close)}")
print(f"unresolved (>5%):  {len(unresolved)}")
print(f"GRAND TOTAL explained: {len(reconciled)}+{len(no_item32)} = "
      f"{(len(reconciled)+len(no_item32))}/{total_n} "
      f"({(len(reconciled)+len(no_item32))/total_n*100:.1f}%)")

for label, bucket in (("close", close), ("unresolved", unresolved)):
    print(f"\n=== {label} ===")
    for code, name, q, it25, total, resid, rel in bucket:
        print(f"  {name}({code}) {q}: item25={it25:,.3f} sum={total:,.3f} "
              f"resid={resid:,.3f} rel={rel:.2%}")
