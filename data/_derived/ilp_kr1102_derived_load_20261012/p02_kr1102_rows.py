# -*- coding: utf-8 -*-
"""Show all KR1102 ILP rows for 2025.4Q / 2026.1Q / 2026.2Q (read-only)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
with open(ROOT + "insurance_liability_portfolio.json", "r", encoding="utf-8") as f:
    d = json.load(f)
rows = [r for r in d if r.get("원보험사코드") == "KR1102"]
print("KR1102 rows:", len(rows))
keys = set()
for r in rows:
    keys.update(r.keys())
print("keys:", sorted(keys))
quarters = sorted({r["공시분기"] for r in rows})
print("quarters:", quarters)
by = {}
for r in rows:
    by.setdefault(r["공시분기"], {})[r["항목번호"]] = r
items = {}
for r in rows:
    items[r["항목번호"]] = (r["항목명"], r["섹션"], r["레벨"])
print("\nitem catalogue:")
for k in sorted(items):
    print(" ", k, items[k])
print("\nper-quarter values:")
for q in quarters:
    print("==", q)
    for k in sorted(by[q]):
        r = by[q][k]
        extra = {kk: vv for kk, vv in r.items() if kk not in ("원보험사코드","원수사명","티커","생손보여부","항목번호","항목명","섹션","레벨","공시분기","값")}
        print("   ", k, r["항목명"], "=", r.get("값"), (extra if extra else ""))
