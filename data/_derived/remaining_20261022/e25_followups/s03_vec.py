# -*- coding: utf-8 -*-
"""READ-ONLY: full 32-item vector (live master, 값 and 값_당분기) of one company over the given quarters, with item names.
usage: s03_vec.py CODE QUARTERS(comma) [ITEMS(comma)]"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
code = sys.argv[1]
qs = sys.argv[2].split(",")
items = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else list(range(1, 41))
rows = [r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == code]
names = {}
for r in rows:
    names.setdefault(r["항목번호"], r.get("항목명"))
by = {(r["공시분기"], r["항목번호"]): r for r in rows}
hdr = "item name".ljust(34) + "".join(q.rjust(26) for q in qs)
print(hdr)
for it in items:
    if it not in names:
        continue
    cells = []
    for q in qs:
        r = by.get((q, it))
        if r is None:
            cells.append("(no row)".rjust(26))
        else:
            v, d = r.get("값"), r.get("값_당분기")
            cells.append((("None" if v is None else f"{v:,.3f}") + "/" + ("None" if d is None else f"{d:,.1f}")).rjust(26))
    print(f"{it:>3} {str(names[it])[:28]:30s}" + "".join(cells))
