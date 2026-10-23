import json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
t = json.load(open("s01_touched.json", encoding="utf-8"))
u = collections.defaultdict(lambda: collections.defaultdict(set))
for k, v in t.items():
    fn, load = k.split("|")
    for cq, items in v.items():
        c, q = cq.split("|")
        u[c][q] |= {(fn[:2], i, load) for i in items}
for c in sorted(u):
    print(c, {q: sorted({l for _,_,l in v}) for q, v in sorted(u[c].items())})
print(sum(len(v) for v in u.values()))
