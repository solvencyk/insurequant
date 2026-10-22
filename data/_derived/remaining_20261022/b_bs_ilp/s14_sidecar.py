import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("data/_derived/ilp_restated_comparative.json", encoding="utf-8"))
print(d.keys())
for c in d["cells"]:
    if c["company_code"] == "KR0073": print(json.dumps(c, ensure_ascii=False)[:1500])
print([ (c["company_code"], c["quarter"]) for c in d["cells"]])
