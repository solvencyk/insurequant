# -*- coding: utf-8 -*-
import json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
def L(p): return json.load(open(p,encoding="utf-8"))
for nm in ("user_pl_cells","user_csm_cells"):
    o=L(HERE+f"head/{nm}.json"); n=L(R+f"data/_gold/{nm}.json")
    print("=====",nm,"top-level keys old/new:",sorted(o.keys()),"|",sorted(n.keys()))
    for k in sorted(set(o)|set(n)):
        if k in ("set",): continue
        if o.get(k)!=n.get(k): print("   top-level key differs:",k, "(len old/new:", len(json.dumps(o.get(k))), len(json.dumps(n.get(k))),")")
    def keyf(e): return (e["원보험사코드"],e["공시분기"],e["항목번호"])
    od={keyf(e):e for e in o["set"]}; nd={keyf(e):e for e in n["set"]}
    print("   set entries old",len(o["set"]),"new",len(n["set"]),"dup keys old/new",len(o["set"])-len(od),len(n["set"])-len(nd))
    added=sorted(set(nd)-set(od)); removed=sorted(set(od)-set(nd)); changed=[k for k in od if k in nd and od[k]!=nd[k]]
    print("   added",len(added),"removed",len(removed),"changed(in place)",len(changed))
    print("   added by company:",dict(collections.Counter(k[0] for k in added)))
    print("   added by company-quarter:",dict(collections.Counter((k[0],k[1]) for k in added)))
    for k in removed: print("   REMOVED",k,od[k])
    print("   -- CHANGED in place --")
    for k in sorted(changed):
        a,b=od[k],nd[k]
        diffs={f:(a.get(f),b.get(f)) for f in set(a)|set(b) if a.get(f)!=b.get(f)}
        print("   ",k,json.dumps(diffs,ensure_ascii=False)[:1200])
    # fields present in added entries
    fs=collections.Counter(tuple(sorted(nd[k].keys())) for k in added)
    print("   fields of added entries:",dict(fs))
    wasset=collections.Counter(("was" in nd[k], nd[k].get("was") is None) for k in added)
    print("   added entries (has 'was', was is None):",dict(wasset))
    if nm=="user_pl_cells":
        for sub in ("null_dangi","set_dangi"):
            ob=o.get(sub,{}); nb=n.get(sub,{})
            oc=[tuple(x[:3]) for x in ob.get("cells",[])]; nc=[tuple(x[:3]) for x in nb.get("cells",[])]
            print("   ",sub,"cells old",len(oc),"new",len(nc),"added",len(set(nc)-set(oc)),"removed",len(set(oc)-set(nc)))
            json.dump({"added":[list(x) for x in sorted(set(nc)-set(oc))],"removed":[list(x) for x in sorted(set(oc)-set(nc))]},open(HERE+f"v21_{sub}.json","w",encoding="utf-8"),ensure_ascii=False)
            if sub=="set_dangi":
                od2={tuple(x[:3]):x for x in ob.get("cells",[])}; nd2={tuple(x[:3]):x for x in nb.get("cells",[])}
                for k in sorted(set(nd2)-set(od2)): print("      set_dangi ADDED",nd2[k])
                for k in sorted(set(od2)-set(nd2)): print("      set_dangi REMOVED",od2[k])
                for k in sorted(set(od2)&set(nd2)):
                    if od2[k]!=nd2[k]: print("      set_dangi CHANGED",od2[k],"->",nd2[k])
    json.dump({"added":[list(k) for k in added],"changed":[list(k) for k in changed],"removed":[list(k) for k in removed]},open(HERE+f"v21_{nm}_delta.json","w",encoding="utf-8"),ensure_ascii=False)
