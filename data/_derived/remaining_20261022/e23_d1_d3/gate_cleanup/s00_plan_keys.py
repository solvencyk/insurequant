import json
P = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/e23_plan_kdb_final.json"
d = json.load(open(P, encoding="utf-8"))
print(type(d), list(d.keys()) if isinstance(d, dict) else len(d))
for k, v in d.items():
    if isinstance(v, list):
        print(k, len(v), json.dumps(v[0], ensure_ascii=False)[:600] if v else None)
    elif isinstance(v, dict):
        print(k, list(v.keys())[:20])
    else:
        print(k, str(v)[:200])
