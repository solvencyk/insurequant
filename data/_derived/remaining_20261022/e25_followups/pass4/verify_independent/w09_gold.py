import json,sys,subprocess
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
new=json.load(open(R+"data/_gold/user_pl_cells.json",encoding="utf-8"))
old=json.loads(subprocess.run(["git","-C",R,"show","HEAD:data/_gold/user_pl_cells.json"],capture_output=True).stdout.decode("utf-8"))
print(type(new), list(new.keys())[:12] if isinstance(new,dict) else len(new))
def cells(g):
    out={}
    for sect,v in g.items():
        if isinstance(v,list):
            for e in v:
                if isinstance(e,dict) and "code" in e or (isinstance(e,dict) and "원보험사코드" in e): out[(sect,json.dumps(e,ensure_ascii=False,sort_keys=True))]=e
    return out
for k in new:
    a,b=old.get(k),new.get(k)
    if a!=b:
        if isinstance(b,list): 
            sa={json.dumps(x,ensure_ascii=False,sort_keys=True) for x in (a or [])}; sb={json.dumps(x,ensure_ascii=False,sort_keys=True) for x in b}
            print("SECTION",k,"len",len(a or []),"->",len(b),"added",len(sb-sa),"removed",len(sa-sb))
            for x in sorted(sb-sa): print("  +",x[:420])
            for x in sorted(sa-sb): print("  -",x[:420])
        else: print("KEY",k,"changed", str(a)[:200],"->",str(b)[:300])
