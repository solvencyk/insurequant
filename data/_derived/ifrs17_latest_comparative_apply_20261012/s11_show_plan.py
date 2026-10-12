import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
p = json.load(open("plan_diff.json", encoding="utf-8"))
print("=== CSM")
for c in p["CSM"]:
    print(c["block"], "item", c["item"], c["old"], "->", c["new"])
print("=== BS")
g = defaultdict(list)
for c in p["BS"]:
    g[c["block"]].append(c)
for b, cs in g.items():
    print(b, [(c["item"], c["old"], c["new"]) for c in cs])
print("=== PL")
g = defaultdict(list)
for c in p["PL"]:
    g[c["block"]].append(c)
for b, cs in g.items():
    print(b)
    for c in cs:
        print("    item", c["item"], c["old"], "->", c["new"])
