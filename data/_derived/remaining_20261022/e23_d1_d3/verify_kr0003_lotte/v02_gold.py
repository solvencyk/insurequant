# -*- coding: utf-8 -*-
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte/v02_gold.txt"
L=[]
def P(*a):
    s=" ".join(str(x) for x in a); L.append(s); print(s)
def head(rel): return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
def live(rel): return json.load(open(R+"/"+rel,encoding="utf-8"))
for rel in ["data/_gold/user_pl_cells.json","data/_gold/user_csm_cells.json"]:
    h,l=head(rel),live(rel)
    P("==",rel)
    for k in sorted(set(h)|set(l)):
        hv,lv=h.get(k),l.get(k)
        if hv==lv: continue
        P("  key",k,"CHANGED",type(lv).__name__, len(hv) if hasattr(hv,"__len__") else hv,"->",len(lv) if hasattr(lv,"__len__") else lv)
        if isinstance(lv,list):
            kf=lambda e:(e.get("원보험사코드"),e.get("항목번호"),e.get("공시분기"))
            hd={kf(e):e for e in hv}; ld={kf(e):e for e in lv}
            P("   dup",len(hv)-len(hd),len(lv)-len(ld))
            add=[x for x in ld if x not in hd]; rem=[x for x in hd if x not in ld]; chg=[x for x in ld if x in hd and ld[x]!=hd[x]]
            P("   added by co",{c:sum(1 for a in add if a[0]==c) for c in sorted(set(a[0] for a in add))},"removed",rem,"changed (any co)",chg)
            P("   KR0003 added:")
            for x in sorted(a for a in add if a[0]=="KR0003"): P("     ",json.dumps(ld[x],ensure_ascii=False))
            P("   KR0003 in HEAD gold, any quarter:", sorted((x[2],x[1]) for x in hd if x[0]=="KR0003"))
            P("   KR0003 changed:", [ (x,json.dumps(hd[x],ensure_ascii=False),json.dumps(ld[x],ensure_ascii=False)) for x in chg if x[0]=="KR0003"])
        elif isinstance(lv,dict):
            ks=[x for x in set(lv)|set(hv or {}) if (hv or {}).get(x)!=lv.get(x)]
            P("   dict keys changed",len(ks),sorted(ks)[:40])
            kr=[x for x in ks if "KR0003" in str(x) or "롯데" in str(x)]
            for x in kr: P("     ",x,json.dumps((hv or {}).get(x),ensure_ascii=False)[:600],"->",json.dumps(lv.get(x),ensure_ascii=False)[:600])
open(OUT,"w",encoding="utf-8").write("\n".join(L))
