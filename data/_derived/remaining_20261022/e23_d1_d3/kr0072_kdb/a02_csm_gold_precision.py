# -*- coding: utf-8 -*-
"""read-only: precision (decimals) of the CSM gold values by company for the chain loads (e21 / e23), to see which stored precision earlier loads used."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
cgold = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))


def dec(v):
    s = repr(float(v))
    return len(s.split(".")[1]) if "." in s and not s.endswith(".0") else 0


from collections import defaultdict
by = defaultdict(list)
for e in cgold["set"]:
    why = str(e.get("why", ""))
    tag = "e23" if "e23" in why else ("e21" if "e21" in why or "20261023T0300Z" in why else ("e20" if "e20" in why else "old"))
    by[(e["원보험사코드"], tag)].append((e["공시분기"], e["항목번호"], e["값"], dec(e["값"])))
for k in sorted(by):
    rows = by[k]
    d = defaultdict(int)
    for r in rows:
        d[r[3]] += 1
    print(k, len(rows), "decimals histogram:", dict(sorted(d.items())))
print()
for key in [("KR0003", "e21"), ("KR0003", "e23"), ("KR0099", "e23"), ("KR0070", "e23"), ("KR0001", "e21"), ("KR0068", "e21"), ("KR0079", "e21")]:
    if key in by:
        print(key, sorted(by[key])[:40])
