import json,sys
sys.stdout.reconfigure(encoding="utf-8")
v=json.load(open("data/dart/viz/csm_waterfall.json",encoding="utf-8"))
print(v["unit"],v["period"],v["stage_labels_ko"])
c=v["companies"]
print(type(c), len(c))
items = c.items() if isinstance(c,dict) else enumerate(c)
for k,x in items:
    s=json.dumps(x,ensure_ascii=False)
    if "한화생명" in s[:300]:
        print(k, list(x.keys()) if isinstance(x,dict) else type(x))
        print(json.dumps(x,ensure_ascii=False)[:6000])
