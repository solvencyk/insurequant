import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
h = json.loads(subprocess.run(["git", "-C", ROOT, "show", "HEAD:PL_breakdown_provenance.json"], capture_output=True).stdout.decode("utf-8"))
l = json.load(open(ROOT + "/PL_breakdown_provenance.json", encoding="utf-8"))
pk = lambda c: (c["company_code"], c["quarter"], c["item_block"])
hm, lm = {pk(c): c for c in h["cells"]}, {pk(c): c for c in l["cells"]}
for k in sorted(lm):
    if hm[k] != lm[k]:
        print("==", k)
        for f in sorted(set(hm[k]) | set(lm[k])):
            if hm[k].get(f) != lm[k].get(f):
                print("  before", f, json.dumps(hm[k].get(f), ensure_ascii=False)[:700])
                print("  after ", f, json.dumps(lm[k].get(f), ensure_ascii=False)[:700])
print([k for k in l if k != "cells"])
for k in l:
    if k.startswith("merge_note"):
        print(k, "HEAD==live:", h.get(k) == l.get(k), "| live:", str(l[k])[:160])
