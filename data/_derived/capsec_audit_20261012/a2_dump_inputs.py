# -*- coding: utf-8 -*-
"""a2: dump the audit inputs for 2026.2Q straight from kics_disclosure.json (read-only).

Independent of the implementation: no imports from scripts/ or src/.
Output: a2_inputs_2026_2Q.csv  (one row per company, pre = 값, post = 값_적용후)
        a2_inputs_2026_2Q.json
Units: 억원 (as stored in the master). Values in the master are strings; '-' / '' / None = missing.
"""
import csv
import json

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/capsec_audit_20261012/"
Q = "2026.2Q"
ITEMS = [1, 2, 3, 6, 13, 14, 15, 27, 28, 47, 48, 49, 50, 51, 52, 53, 54]


def num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s in ("", "-", "—", "–", "nan", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return ("RAW", s)


import sys
sys.path.insert(0, OUT)
import audit_io
d = audit_io.load_json("kics_disclosure.json")
rows = {}
dup = []
for r in d:
    if r.get("공시분기") != Q:
        continue
    k = r.get("항목번호")
    if k not in ITEMS:
        continue
    code = r["원보험사코드"]
    c = rows.setdefault(code, {"code": code, "name": r["원수사명"], "type": r.get("생손보여부")})
    key_pre = "i%d_pre" % k
    key_post = "i%d_post" % k
    if key_pre in c:
        dup.append((code, k))
    c[key_pre] = num(r.get("값"))
    c[key_post] = num(r.get("값_적용후"))

cols = ["code", "name", "type"]
for k in ITEMS:
    cols += ["i%d_pre" % k, "i%d_post" % k]
with open(OUT + "a2_inputs_2026_2Q.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for code in sorted(rows):
        w.writerow([rows[code].get(c) for c in cols])
json.dump(rows, open(OUT + "a2_inputs_2026_2Q.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("companies", len(rows), "dups", dup)
bad = [(c, k, v) for c, row in rows.items() for k, v in row.items() if isinstance(v, tuple)]
print("non-numeric raw cells", bad)
