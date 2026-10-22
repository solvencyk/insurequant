# -*- coding: utf-8 -*-
import json, csv, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
HERE = ROOT + "data/_derived/remaining_20261022/e21_ready25/verify/"
recs = json.load(open(HERE + "v07_cites.json", encoding="utf-8"))
master = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in json.load(open(ROOT + "PL_breakdown.json", encoding="utf-8"))}
head = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in json.load(open(HERE + "head/PL_breakdown.json", encoding="utf-8"))}
rows = list(csv.DictReader(open(ROOT + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv", encoding="utf-8-sig")))
csvidx = {(r["code"], r["quarter"], int(r["item"])): r for r in rows if r["sheet"] == "PL"}
by = collections.defaultdict(list)
for c in recs:
    by[tuple(c["key"])].append(c)
sign = collections.defaultdict(collections.Counter)
mism = []
n_direct = 0
for k, cs in sorted(by.items()):
    how = csvidx[k]["how"]
    m = master[k]["값"]
    if how.startswith("statement") or how.startswith("note table"):
        n_direct += 1
        vals = {round(c["val_mn"], 6) for c in cs}
        if len(vals) > 1:
            mism.append((k, "multi-values", vals, m)); continue
        v = vals.pop()
        if abs(abs(m) - abs(v)) > 1e-4 + 1e-9 * abs(v):
            mism.append((k, "value", v, m, how)); continue
        s = 0 if v == 0 else (1 if (m > 0) == (v > 0) else -1)
        sign[(k[0], k[2])][s] += 1
print("direct cells with cites:", n_direct, "mismatch:", len(mism))
for x in mism: print(x)
print("sign relation (master vs printed) by company,item where mixed or -1:")
for k, c in sorted(sign.items()):
    if -1 in c:
        print(k, dict(c))
