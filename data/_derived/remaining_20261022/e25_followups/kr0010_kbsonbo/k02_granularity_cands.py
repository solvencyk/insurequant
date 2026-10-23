# -*- coding: utf-8 -*-
"""READ-ONLY: how did KR0010 item 16 2024.4Q / 2025.2Q get 60,900 / 33,300 (2026-10-11 granularity load)? prints the candidate entries from pl_candidates/KR0010.json for item 16 and the manifest context."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
B = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/bspl_granularity_20261011"
d = json.load(open(f"{B}/pl_candidates/KR0010.json", encoding="utf-8"))
print(type(d).__name__, list(d.keys())[:20] if isinstance(d, dict) else len(d))
def walk(o, path=""):
    if isinstance(o, dict):
        if o.get("item") == 16 or o.get("항목번호") == 16 or str(o.get("label", "")).replace(" ", "").endswith("기타사업비용"):
            print(path, json.dumps(o, ensure_ascii=False)[:900])
        for k, v in o.items():
            walk(v, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + f"[{i}]")
walk(d)
m = json.load(open(f"{B}/load_manifest_pl.json", encoding="utf-8"))
print("manifest keys:", list(m.keys()))
for k, v in m.items():
    if isinstance(v, list) and any("KR0010|16" in str(x) for x in v):
        print(k, [x for x in v if "KR0010|16" in str(x)])
    elif isinstance(v, dict):
        for k2, v2 in v.items():
            if "KR0010|16" in str(k2) or (isinstance(v2, (dict, list)) and "KR0010|16" in json.dumps(v2, ensure_ascii=False)):
                print(k, k2, json.dumps(v2, ensure_ascii=False)[:600])
