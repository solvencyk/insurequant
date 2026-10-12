# -*- coding: utf-8 -*-
"""Read-only: KR1107 CSM_waterfall rows (all quarters) + provenance cells."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
root = "C:/Users/sangwook.cho/Desktop/insurequant/"
wf = json.loads(open(root + "CSM_waterfall.json", "rb").read().decode("utf-8"))
for r in wf:
    if r["원보험사코드"] == "KR1107":
        print(r["공시분기"], r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"))
