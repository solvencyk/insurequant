# -*- coding: utf-8 -*-
"""diff. Read-only."""
import json, subprocess, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte/"
def head(rel):
    b=subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout
    return json.loads(b.decode("utf-8"))
def live(rel):
    return json.load(open(R+"/"+rel,encoding="utf-8"))
lines=[]
def P(*a):
    s=" ".join(str(x) for x in a); lines.append(s); print(s)
K=lambda r:(r["원보험사코드"],r["항목번호"],r["공시분기"])
for rel in ["PL_breakdown.json","CSM_waterfall.json"]:
    h=head(rel); l=live(rel)
    P("==",rel,"rows head",len(h),"live",len(l))
    hk=[K(r) for r in h]; lk=[K(r) for r in l]
    P("dup keys head/live:",len(hk)-len(set(hk)),len(lk)-len(set(lk)))
    hs=set(hk); ls=set(lk)
    P("rows added:",[k for k in ls-hs if k[0]=="KR0003"],"count all added",len(ls-hs),"removed",len(hs-ls))
    P("added KR0003:",sorted(k for k in ls-hs if k[0]=="KR0003"), "removed KR0003:",sorted(k for k in hs-ls if k[0]=="KR0003"))
    hm={K(r):r for r in h}; lm={K(r):r for r in l}
    cnt=collections.Counter(); other=collections.Counter(); chg=[]
    for k in ls&hs:
        a,b=hm[k],lm[k]
        if a==b: continue
        for f in set(a)|set(b):
            if a.get(f)!=b.get(f):
                if k[0]=="KR0003": cnt[(k[2],f)]+=1; chg.append((k,f,a.get(f),b.get(f)))
                else: other[(k[0],f)]+=1
    P("KR0003 changes per (quarter,field):",dict(sorted(cnt.items())))
    P("other-company changes (ignored):",sorted(set(c for c,_ in other)))
    P("KR0003 changes outside 2023.1Q-3Q:",[c for c in chg if c[0][2] not in ("2023.4Q",)][:30])
    json.dump([[list(k),f,o,n] for k,f,o,n in sorted(chg)],open(OUT+"v01_changes_"+rel.split(".")[0]+".json","w",encoding="utf-8"),ensure_ascii=False)
    for c in sorted(chg): P("  ",c[0][2],c[0][1],c[1],c[2],"->",c[3])
# provenance
for rel in ["PL_breakdown_provenance.json","CSM_waterfall_provenance.json"]:
    h=head(rel); l=live(rel)
    P("==",rel)
    P("top-level keys added",sorted(set(l)-set(h)),"removed",sorted(set(h)-set(l)),"changed non-cells",[k for k in l if k in h and k!="cells" and l[k]!=h[k]])
    hc=h["cells"]; lc=l["cells"]
    P("cells head",len(hc),"live",len(lc))
    def kk(c): return (c.get("company_code"),c.get("quarter"),c.get("item_block"))
    hd={kk(c):c for c in hc}; ld={kk(c):c for c in lc}
    P("dupe keys head/live",len(hc)-len(hd),len(lc)-len(ld))
    P("blocks added",[k for k in ld if k not in hd],"removed",[k for k in hd if k not in ld])
    ch=[k for k in ld if k in hd and ld[k]!=hd[k]]
    P("changed blocks total",len(ch),"KR0003",sorted(k for k in ch if k[0]=="KR0003"),"other co",sorted(set(k[0] for k in ch if k[0]!="KR0003")))
    for k in sorted(k for k in ch if k[0]=="KR0003"):
        a,b=hd[k],ld[k]
        P("  BLOCK",k)
        for f in sorted(set(a)|set(b)):
            if a.get(f)!=b.get(f): P("     ",f,"\n        OLD:",json.dumps(a.get(f),ensure_ascii=False)[:700],"\n        NEW:",json.dumps(b.get(f),ensure_ascii=False)[:700])
open(OUT+"v01_diff.txt","w",encoding="utf-8").write("\n".join(lines))
