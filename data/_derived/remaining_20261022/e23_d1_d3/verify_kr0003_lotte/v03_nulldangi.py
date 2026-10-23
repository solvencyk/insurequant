# -*- coding: utf-8 -*-
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
h=json.loads(subprocess.run(["git","-C",R,"show","HEAD:data/_gold/user_pl_cells.json"],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
l=json.load(open(R+"/data/_gold/user_pl_cells.json",encoding="utf-8"))
a=h["null_dangi"]; b=l["null_dangi"]
print("keys",list(a),"->",list(b))
for k in b:
    if a.get(k)!=b[k]:
        print("CHANGED",k, type(b[k]).__name__)
        if k=="cells":
            ha=a.get(k) or []; 
            print(" head cells",len(ha),"live",len(b[k]))
            sh=json.dumps(ha,sort_keys=True)
            for e in b[k]:
                if e not in ha: print("  +",json.dumps(e,ensure_ascii=False)[:300])
            print("  removed:",[e for e in ha if e not in b[k]])
        else: print(str(b[k])[:900])
# other top-level keys of gold
for k in l:
    if k in ("set","null_dangi"): continue
    print("top",k,"same" if h.get(k)==l[k] else "DIFF")
print("set non-list keys", [k for k in l["set"]][:3] if isinstance(l["set"],dict) else "list")
