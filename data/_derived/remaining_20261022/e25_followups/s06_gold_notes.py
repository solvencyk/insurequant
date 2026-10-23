# -*- coding: utf-8 -*-
"""READ-ONLY: full gold `set` entries (PL) for given code/quarter/items; usage: s06_gold_notes.py CODE QUARTER ITEM[,ITEM...]"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
code, q, items = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")]
g = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_gold/user_pl_cells.json", encoding="utf-8"))
print("top-level keys:", list(g.keys()))
for e in g["set"]:
    if e["원보험사코드"] == code and e["공시분기"] == q and e["항목번호"] in items:
        print(json.dumps(e, ensure_ascii=False, indent=1))
