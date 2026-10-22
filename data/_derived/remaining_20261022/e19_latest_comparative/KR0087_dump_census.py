# -*- coding: utf-8 -*-
import json, csv, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = ROOT / "data/_derived/remaining_20261022/d_census"
OUT = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
lines = []
with open(D / "d_census_table.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["code"] == "KR0087":
            lines.append("CSV " + json.dumps(r, ensure_ascii=False))
with open(D / "d_census_addl.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["code"] == "KR0087":
            lines.append("ADDL " + json.dumps(r, ensure_ascii=False))
b = json.loads((D / "d5_buckets.json").read_text(encoding="utf-8"))
lines.append("d5 type %s" % type(b).__name__)
if isinstance(b, dict):
    ks = [k for k in b if "KR0087" in k]
    lines.append("d5 keys " + str(ks))
    for k in ks:
        lines.append("D5 " + k + " " + json.dumps(b[k], ensure_ascii=False)[:6000])
else:
    for x in b:
        if x.get("code") == "KR0087":
            lines.append("D5 " + json.dumps(x, ensure_ascii=False)[:6000])
c = json.loads((D / "cand_pl_cells.json").read_text(encoding="utf-8"))
lines.append("cand type %s" % type(c).__name__)
s = json.dumps(c, ensure_ascii=False)
lines.append("cand head " + s[:600])
(OUT / "KR0087_census_dump.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
