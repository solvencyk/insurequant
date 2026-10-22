import json, subprocess, sys, io
out = io.open("data/_derived/remaining_20261022/v_oci/scope_diff.txt","w",encoding="utf-8")
def P(*a):
    s=" ".join(str(x) for x in a); out.write(s+"\n")
def head(path):
    b=subprocess.run(["git","show","HEAD:"+path],capture_output=True,check=True).stdout
    return json.loads(b.decode("utf-8"))
def cur(path):
    return json.load(open(path,encoding="utf-8"))
# --- master
h=head("PL_breakdown.json"); c=cur("PL_breakdown.json")
def idx(rows):
    d={}
    for r in rows:
        k=(r["원보험사코드"],r["항목번호"],r["공시분기"])
        assert k not in d, k
        d[k]=r
    return d
hi,ci=idx(h),idx(c)
P("rows head/cur",len(h),len(c),"keys only head",len(set(hi)-set(ci)),"keys only cur",len(set(ci)-set(hi)))
changes=[]
for k in sorted(set(hi)|set(ci),key=lambda t:tuple(map(str,t))):
    a,b=hi.get(k),ci.get(k)
    if a==b: continue
    fields=set(a or {})|set(b or {})
    diff={f:(a or {}).get(f,"<absent>") for f in fields if (a or {}).get(f,"<absent>")!=(b or {}).get(f,"<absent>")}
    diff={f:(diff[f],(b or {}).get(f,"<absent>")) for f in diff}
    changes.append((k,diff))
P("changed rows",len(changes))
comp=set(); quarters=set(); items=set(); fields=set()
for k,d in changes:
    comp.add(k[0]); quarters.add(k[2]); items.add(k[1]); fields|=set(d)
    P(k,d)
P("companies",comp,"quarters",sorted(quarters),"items",sorted(items,key=str),"fields",fields)
# top-level order / non-row differences
P("key order identical (list order):",[ (r["원보험사코드"],r["항목번호"],r["공시분기"]) for r in h]==[(r["원보험사코드"],r["항목번호"],r["공시분기"]) for r in c])
# --- provenance
hp=head("PL_breakdown_provenance.json"); cp=cur("PL_breakdown_provenance.json")
P("PROV top-level keys added",set(cp)-set(hp),"removed",set(hp)-set(cp))
for k in set(hp)&set(cp):
    if k!="cells" and hp[k]!=cp[k]: P("PROV top-level changed",k)
def pidx(cells):
    d={}
    for x in cells:
        kk=(x["company_code"],x["quarter"],x["item_block"]); assert kk not in d; d[kk]=x
    return d
ph,pc=pidx(hp["cells"]),pidx(cp["cells"])
P("prov cells head/cur",len(ph),len(pc),"only head",set(ph)-set(pc),"only cur",set(pc)-set(ph))
for k in sorted(set(ph)|set(pc)):
    if ph.get(k)!=pc.get(k):
        P("PROV CHANGED",k)
        P("  head",json.dumps(ph.get(k),ensure_ascii=False))
        P("  cur ",json.dumps(pc.get(k),ensure_ascii=False))
# --- gold
gh=head("data/_gold/user_pl_cells.json"); gc=cur("data/_gold/user_pl_cells.json")
P("GOLD top keys head",list(gh),"cur",list(gc))
for k in gc:
    if gh.get(k)!=gc.get(k) and k not in ("set","null_dangi","set_dangi"): P("GOLD non-cell key changed",k, str(gh.get(k))[:100], str(gc.get(k))[:100])
def skey(x): return (x["원보험사코드"],x["항목번호"],x["공시분기"])
sh={skey(x):x for x in gh["set"]}; sc={skey(x):x for x in gc["set"]}
P("GOLD set head/cur",len(gh["set"]),len(gc["set"]),"removed",set(sh)-set(sc))
added=sorted(set(sc)-set(sh)); P("GOLD set added",len(added))
for k in added: P("  +",k,sc[k]["값"],"was",sc[k].get("was"))
modified=[k for k in set(sh)&set(sc) if sh[k]!=sc[k]]; P("GOLD set modified existing",modified)
for k in modified: P("  mod",k,sh[k],sc[k])
# list order preserved?
P("GOLD set head prefix preserved:", gc["set"][:len(gh["set"])]==gh["set"])
for sec in ("null_dangi","set_dangi"):
    a=gh.get(sec); b=gc.get(sec)
    P(sec,"head",json.dumps(a,ensure_ascii=False)[:300] if a else a)
    if isinstance(a,dict) and isinstance(b,dict):
        ha=[tuple(x) if isinstance(x,list) else x for x in a.get("cells",[])]
        hb=[tuple(x) if isinstance(x,list) else x for x in b.get("cells",[])]
        P(sec,"cells head/cur",len(ha),len(hb),"removed",[x for x in ha if x not in hb])
        P(sec,"added",[x for x in hb if x not in ha])
        P(sec,"other keys changed",[k for k in set(a)|set(b) if k!="cells" and a.get(k)!=b.get(k)])
out.close()
