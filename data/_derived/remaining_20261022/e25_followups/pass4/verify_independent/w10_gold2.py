import json,sys,subprocess
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
new=json.load(open(R+"data/_gold/user_pl_cells.json",encoding="utf-8"))
old=json.loads(subprocess.run(["git","-C",R,"show","HEAD:data/_gold/user_pl_cells.json"],capture_output=True).stdout.decode("utf-8"))
k=lambda e:(e["원보험사코드"],e["공시분기"],e["항목번호"])
o={k(e):e for e in old["set"]}; n={k(e):e for e in new["set"]}
print("added estimate flags:",{kk:n[kk].get("estimate") for kk in n if kk not in o})
print("all-set estimate True count old/new",sum(1 for e in old["set"] if e.get("estimate")),sum(1 for e in new["set"] if e.get("estimate")))
for sec in ("null_dangi","set_dangi"):
    a,b=old[sec],new[sec]
    print(sec,type(a).__name__,len(a),"->",len(b))
    if isinstance(b,dict):
        for kk in b:
            if kk not in a: print("  + key",kk, str(b[kk])[:200])
            elif a[kk]!=b[kk]: print("  ~ key",kk,str(a[kk])[:120],"->",str(b[kk])[:200])
        for kk in a:
            if kk not in b: print("  - key",kk)
