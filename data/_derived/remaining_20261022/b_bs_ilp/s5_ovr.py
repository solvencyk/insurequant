import json,sys
sys.stdout.reconfigure(encoding="utf-8")
d=json.load(open("data/dart/viz/bs_manual_overrides.json",encoding="utf-8"))
print(json.dumps(d["_readme"],ensure_ascii=False)[:3000])
print(list(d["_removed"])[:3] if isinstance(d["_removed"],(list,dict)) else d["_removed"])
for k,v in d["cells"].items():
    if k.startswith("KR0073"):
        print(k); print(json.dumps(v,ensure_ascii=False,indent=1))
