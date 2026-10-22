import json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
rows=json.load(open("v30_rows.json",encoding="utf-8"))
bad=[r for r in rows if not r[6]]
bycq=collections.defaultdict(list)
for r in bad: bycq[(r[0],r[1])].append(r)
for k,v in sorted(bycq.items()):
    kinds=collections.Counter("master-blank" if r[3] is None else "differs" for r in v)
    print(k,dict(kinds),[ (r[2],r[3],round(r[5],3)) for r in v if r[3] is not None][:8])
# improved vs worse: cells where old matched but new doesn't
worse=[r for r in rows if r[7] and not r[6]]
better=[r for r in rows if r[6] and not r[7]]
print("cells matching printed prior-cum in HEAD but NOT in NEW (regressions):",len(worse),worse[:10])
print("cells that newly match printed prior-cum (HEAD did not):",len(better))
print("both match:",sum(1 for r in rows if r[6] and r[7]))
