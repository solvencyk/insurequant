# -*- coding: utf-8 -*-
import json, subprocess, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")
ROOT="C:/Users/sangwook.cho/Desktop/insurequant"
def head(p):
    return subprocess.run(["git","-C",ROOT,"show","HEAD:"+p],capture_output=True).stdout
def load_b(b): return json.loads(b.decode("utf-8"))
old=load_b(head("PL_breakdown.json"))
new=json.load(open(ROOT+"/PL_breakdown.json",encoding="utf-8"))
def idx(rows):
    d={}
    for r in rows:
        k=(r["원보험사코드"],r["공시분기"],r["항목번호"])
        assert k not in d,k
        d[k]=r
    return d
O,N=idx(old),idx(new)
print("rows",len(O),len(N))
print("added keys",[k for k in N if k not in O][:10],"removed",[k for k in O if k not in N][:10])
ch=[]
for k in sorted(set(O)|set(N),key=lambda k:tuple(str(x) for x in k)):
    a,b=O.get(k),N.get(k)
    if a==b: continue
    fa=set(a or {})|set(b or {})
    for f in sorted(fa):
        va=(a or {}).get(f); vb=(b or {}).get(f)
        if va!=vb: ch.append((k,f,va,vb))
print("changed fields",len(ch))
for k,f,va,vb in ch: print(k,f,va,"->",vb)
json.dump([[list(k),f,va,vb] for k,f,va,vb in ch],open(ROOT+"/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/w01_changes.json","w",encoding="utf-8"),ensure_ascii=False)
# byte compare of other files
for p in ["CSM_waterfall.json","CSM_waterfall_provenance.json","gold_overlay_ledger.json","data/_gold/gold_overlay_ledger.json","data/_gold/user_csm_cells.json"]:
    try:
        h=hashlib.sha256(head(p)).hexdigest()
        cur=hashlib.sha256(open(ROOT+"/"+p,"rb").read()).hexdigest()
        print(p,"same" if h==cur else "DIFF")
    except Exception as e: print(p,"ERR",e)
