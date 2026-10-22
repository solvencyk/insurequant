# -*- coding: utf-8 -*-
"""d7: per company x FY: status of every quarter vs the latest comparative (master vs later-filing prior column, Tier-1 items 1,17,22,24,25,31).
EQ = master equals the latest; DIFF = master differs; NOPRIOR = no later filing/cache with a prior column (cannot judge); SIGN = only sign artifacts."""
import json, sys
from pathlib import Path
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
res = json.loads((OUT / "d1_scan.json").read_text(encoding="utf-8"))
RES = {(r["code"], r["q"]): r for r in res}
def near(a, b, floor=200.0): return abs(a - b) <= max(0.001 * abs(b), floor)
st = {}
for (code, q), r in RES.items():
    diffs = []
    for i in ("1", "17", "22", "24", "25", "31"):
        v = r["items"].get(i)
        if not v or v["master"] is None or v["prior"] is None: continue
        if not near(v["master"], v["prior"]): diffs.append(i)
    st[(code, q)] = ("DIFF" if diffs else "EQ", diffs, r["div_same"])
names = {r["code"]: r["name"] for r in res}
setA = set(map(tuple, json.loads((OUT / "d5_setA.json").read_text(encoding="utf-8"))))
codes = sorted({c for c, _ in setA})
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q"]
lines = []
for c in codes:
    row = []
    for q in QS:
        s = st.get((c, q))
        row.append(f"{q[2:]}:{'--' if s is None else s[0]}{'*' if (c, q) in setA else ''}")
    lines.append(f"{names[c][:9]:10s} " + " ".join(row))
txt = "\n".join(lines)
print(txt)
(OUT / "d7_fyblocks.txt").write_text("legend: EQ = master equals later-filing prior column; DIFF = differs (items 1,17,22,24,25,31); '--' = no later-filing prior column parsed; * = in the 51-bucket list\n" + txt + "\n", encoding="utf-8")
json.dump({f"{c}|{q}": v for (c, q), v in st.items()}, open(OUT / "d7_status.json", "w", encoding="utf-8"), ensure_ascii=False)
