import json, sys
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
d = json.loads(open(M + "cands_N6_HD_FY2023.json", encoding="utf-8").read())
from collections import defaultdict
by = defaultdict(list)
for c in d["pl_cells"]:
    by[c["q"]].append(c["item"])
for q, its in by.items():
    print("PL", q, sorted(its))
by = defaultdict(list)
for c in d["csm_cells"]:
    by[c["q"]].append((c["item"], c["old"], c["new"]))
for q, its in by.items():
    print("CSM", q, its)
print(d["log"][:6])
