"""a1_cell_classes: item distribution of the READY_all candidate cells per bucket (READ-ONLY)"""
import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
d = json.loads(open(M + "cands_READY_all.json", encoding="utf-8").read())
by = defaultdict(list)
for c in d["pl_cells"]:
    by[(c["code"], c["q"])].append(c["item"])
for k in sorted(by):
    print(k, len(by[k]), sorted(by[k]))
print("CSM:")
bc = defaultdict(list)
for c in d["csm_cells"]:
    bc[(c["code"], c["q"])].append(c["item"])
for k in sorted(bc):
    print(k, len(bc[k]), sorted(bc[k]))
print(len(d["pl_cells"]), len(d["csm_cells"]))
