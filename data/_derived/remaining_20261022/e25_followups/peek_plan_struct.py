# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl/e23_plan_abl_final.json", encoding="utf-8"))
print(list(p.keys()))
for k, v in p.items():
    if isinstance(v, dict):
        print(k, "dict", list(v.keys())[:30])
    elif isinstance(v, list):
        print(k, "list", len(v), (json.dumps(v[0], ensure_ascii=False)[:600] if v else ""))
    else:
        print(k, type(v).__name__, str(v)[:200])
C = p["apply_contract"]
for k, v in C.items():
    if isinstance(v, list):
        print("C", k, len(v), (json.dumps(v[0], ensure_ascii=False)[:900] if v else ""))
    else:
        print("C", k, str(v)[:200])
