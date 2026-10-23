# -*- coding: utf-8 -*-
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
def head(rel): return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
def live(rel): return json.load(open(R+"/"+rel,encoding="utf-8"))
for rel in ["data/_gold/user_pl_cells.json","data/_gold/user_csm_cells.json","data/_gold/gold_overlay_ledger.json"]:
    h,l=head(rel),live(rel)
    print("==",rel,"top keys head",list(h) if isinstance(h,dict) else type(h),"live",list(l) if isinstance(l,dict) else type(l))
    if not isinstance(h,dict): continue
    for k in l:
        hv,lv=h.get(k),l[k]
        if hv==lv: print("  key",k,"UNCHANGED", len(lv) if hasattr(lv,"__len__") else lv); continue
        print("  key",k,"CHANGED", type(lv).__name__, len(hv) if hv is not None and hasattr(hv,"__len__") else None,"->",len(lv) if hasattr(lv,"__len__") else lv)
        if isinstance(lv,list):
            # entries keyed by 원보험사코드/항목번호/공시분기
            kf=lambda e:(e.get("원보험사코드"),e.get("항목번호"),e.get("공시분기"))
            hd={kf(e):e for e in hv}; ld={kf(e):e for e in lv}
            print("   dup keys head/live",len(hv)-len(hd),len(lv)-len(ld))
            add=[k2 for k2 in ld if k2 not in hd]; rem=[k2 for k2 in hd if k2 not in ld]; chg=[k2 for k2 in ld if k2 in hd and ld[k2]!=hd[k2]]
            print("   added",len(add),"by co",{c:sum(1 for a in add if a[0]==c) for c in sorted(set(a[0] for a in add))},"removed",len(rem),"changed",len(chg))
            print("   changed keys:",chg[:20], " removed:",rem[:10])
            kb=[ld[a] for a in add if a[0]=="KR0099"]
            print("   KR0099 added entries:",len(kb))
            for e in sorted(kb,key=lambda e:(e["공시분기"],e["항목번호"])): print("     ",json.dumps(e,ensure_ascii=False)[:420])
            print("   order preserved (head is prefix of live):", [kf(e) for e in lv[:len(hv)]]==[kf(e) for e in hv] and all(lv[i]==hv[i] for i in range(len(hv))) )
        elif isinstance(lv,dict):
            print("   dict keys changed", [x for x in set(lv)|set(hv or {}) if (hv or {}).get(x)!=lv.get(x)][:20])
