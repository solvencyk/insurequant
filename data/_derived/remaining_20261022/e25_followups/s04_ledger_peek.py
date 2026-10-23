# -*- coding: utf-8 -*-
"""READ-ONLY: gold_overlay_ledger.json entries whose key contains the given substring(s). usage: s04_ledger_peek.py SUBSTR [SUBSTR...]"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_gold/gold_overlay_ledger.json", encoding="utf-8"))
print("top keys:", list(d.keys()))
e = d["entries"]
print("n entries:", len(e))
for k, v in sorted(e.items()):
    if all(s in k for s in sys.argv[1:]):
        print(k, json.dumps(v, ensure_ascii=False)[:700])
