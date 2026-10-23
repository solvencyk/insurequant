# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
a = json.load(open(ROOT + "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0003_lotte/extra/data/_derived/qoq_warn.json", encoding="utf-8"))
b = json.load(open(ROOT + "data/_derived/qoq_warn.json", encoding="utf-8"))
print("type", type(a).__name__, "len", len(a), "->", len(b))
def key(e): return (e["company"], e["quarter"], e["item"], e.get("basis"))
ma, mb = {key(e): e for e in a}, {key(e): e for e in b}
print("only before:", [(k[0], k[1], k[2]) for k in ma if k not in mb])
print("only after :", [(k[0], k[1], k[2]) for k in mb if k not in ma])
for k in ma:
    if k in mb and ma[k] != mb[k]:
        print("changed:", k, {f: (ma[k][f], mb[k][f]) for f in ma[k] if ma[k][f] != mb[k][f]})
