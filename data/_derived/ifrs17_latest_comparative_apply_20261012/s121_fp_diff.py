import json, sys
a = json.load(open(sys.argv[1], encoding="utf-8")); b = json.load(open(sys.argv[2], encoding="utf-8"))
print("sheets before/after:", len(a), len(b))
for k in sorted(set(a) | set(b)):
    if a.get(k) != b.get(k):
        print("CHANGED:", k, a.get(k, {}).get("rows"), "->", b.get(k, {}).get("rows"))
print("unchanged sheets:", sum(1 for k in a if a.get(k) == b.get(k)))
