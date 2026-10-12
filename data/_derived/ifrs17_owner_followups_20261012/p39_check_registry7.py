# -*- coding: utf-8 -*-
"""Read-only: are the 7 withheld cells registered in data/_gold/user_pl_confirmed_cells.json ?"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
reg = json.loads(open(R + "data/_gold/user_pl_confirmed_cells.json", "rb").read().decode("utf-8"))
ents = reg["cells"]
print("entries:", len(ents), "| masters:", sorted({e["master"] for e in ents}))
for e in ents:
    if e["master"] == "PL_breakdown":
        print(e["company"], "|", e["item"], "|", e["quarter"], "|", e["value"], "|", str(e["note"])[:60])
