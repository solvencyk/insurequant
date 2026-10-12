# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ev = json.loads(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_owner_followups_20261012/amort_split_evidence.json", "rb").read().decode("utf-8"))
h = [e for e in ev if e["code"] == "KR0068"][0]
for k, v in h.items():
    if k == "cells":
        continue
    print(k, ":", json.dumps(v, ensure_ascii=False)[:600])
print([ (c["경과차년"], c["old"], c["new"]) for c in h["cells"]])
for e in ev:
    if e["code"] != "KR0068":
        print(e["code"], "pairs_found", e["pairs_found"], "cur lines", e["current"]["front_line"], e["current"]["back_line"], "prior lines", None if not e["prior"] else (e["prior"]["front_line"], e["prior"]["back_line"]), "y11+ (eok)", e["y11plus_eok"], "consolidated", e.get("consolidated"))
