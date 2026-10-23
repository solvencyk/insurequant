# -*- coding: utf-8 -*-
"""pass2 s05 (read-only): print the full PL (or CSM) gold `set` entries for a company/item/quarters.
usage: s05_gold_entry.py PL|CSM CODE ITEM[,ITEM..] [QUARTERS comma list | all]"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
kind, code = sys.argv[1], sys.argv[2]
items = [int(x) for x in sys.argv[3].split(",")]
qs = None if len(sys.argv) < 5 or sys.argv[4] == "all" else sys.argv[4].split(",")
f = "user_pl_cells.json" if kind == "PL" else "user_csm_cells.json"
g = json.load(open(f"{ROOT}/data/_gold/{f}", encoding="utf-8"))
for e in g["set"]:
    if e["원보험사코드"] == code and e["항목번호"] in items and (qs is None or e["공시분기"] in qs):
        print(json.dumps(e, ensure_ascii=False, indent=1))
