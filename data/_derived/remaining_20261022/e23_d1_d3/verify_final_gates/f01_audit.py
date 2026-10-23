# -*- coding: utf-8 -*-
"""Cell-count audit vs git HEAD. Read-only."""
import json, subprocess, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_final_gates/"
def head(rel):
    b=subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout
    return json.loads(b.decode("utf-8"))
def live(rel): return json.load(open(R+"/"+rel,encoding="utf-8"))
K=lambda r:(r["원보험사코드"],r["항목번호"],r["공시분기"])
FIVE={"KR0099":(60,15),"KR0003":(18,5),"KR0070":(74,20),"KR0009":(57,18),"KR0072":(65,20)}
lines=[]
def P(*a):
    s=" ".join(str(x) for x in a); lines.append(s); print(s)
res={}
for rel,idx in (("PL_breakdown.json",0),("CSM_waterfall.json",1)):
    h=head(rel); l=live(rel)
    hm={K(r):r for r in h}; lm={K(r):r for r in l}
    P("==",rel,"head rows",len(h),"live rows",len(l),"dupkeys",len(h)-len(hm),len(l)-len(lm))
    P("rows added",len(set(lm)-set(hm)),"removed",len(set(hm)-set(lm)))
    per=collections.defaultdict(lambda: collections.Counter())
    cells=collections.defaultdict(set)
    for k in set(hm)|set(lm):
        a=hm.get(k); b=lm.get(k)
        if a is None or b is None:
            per[k[0]]["row_add_or_remove"]+=1; cells[k[0]].add(k); continue
        for f in set(a)|set(b):
            if a.get(f)!=b.get(f):
                per[k[0]][f]+=1
                cells[k[0]].add(k)
    for c in sorted(per):
        P(c, "rows-with-change", len(cells[c]), dict(per[c]), "expected" if c in FIVE else "UNEXPECTED", FIVE.get(c,(None,None))[idx])
    res[rel]={c:sorted(cells[c]) for c in cells}
    # 값 changes by quarter for five
    for c in FIVE:
        q=collections.Counter(); 
        for k in cells[c]:
            if hm.get(k) and lm.get(k) and hm[k].get("값")!=lm[k].get("값"): q[k[2]]+=1
        P("  ",c,"값-changed cells per quarter",dict(sorted(q.items())), "total", sum(q.values()))
json.dump(res,open(OUT+"f01_changed_cells.json","w",encoding="utf-8"),ensure_ascii=False)
open(OUT+"f01_audit.txt","w",encoding="utf-8").write("\n".join(lines))
