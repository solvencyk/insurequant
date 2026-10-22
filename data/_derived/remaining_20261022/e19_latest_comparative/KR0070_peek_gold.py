# -*- coding: utf-8 -*-
import json
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
O = R/"data/_derived/remaining_20261022/e19_latest_comparative"
L=[]
p = R/"data/_gold/user_pl_confirmed_cells.json"
d = json.loads(p.read_text(encoding="utf-8"))
L.append("confirmed type "+type(d).__name__+" keys "+str(list(d.keys()) if isinstance(d,dict) else len(d)))
s = json.dumps(d,ensure_ascii=False)
L.append("KR0070 mentions in confirmed: %d" % s.count("KR0070"))
def walk(x,path=""):
    if isinstance(x,dict):
        if x.get("원보험사코드")=="KR0070" or x.get("code")=="KR0070":
            L.append("  "+path+" "+json.dumps(x,ensure_ascii=False)[:300])
        for k,v in x.items(): walk(v,path+"/"+str(k))
    elif isinstance(x,list):
        for i,v in enumerate(x):
            if isinstance(v,list) and "KR0070" in v: L.append("  "+path+f"[{i}] "+json.dumps(v,ensure_ascii=False)[:300])
            else: walk(v,path+f"[{i}]")
walk(d)
g = json.loads((R/"data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
L.append("user_pl_cells null_dangi doc: "+json.dumps(g["null_dangi"].get("_doc"),ensure_ascii=False)[:600])
L.append("user_pl_cells null_dangi cells n=%d ; set_dangi cells n=%d"%(len(g["null_dangi"]["cells"]),len(g["set_dangi"]["cells"])))
L.append("set_dangi sample "+json.dumps(g["set_dangi"]["cells"][:3],ensure_ascii=False))
L.append("null_dangi sample "+json.dumps(g["null_dangi"]["cells"][:3],ensure_ascii=False))
L.append("set_dangi doc "+json.dumps(g["set_dangi"].get("_doc"),ensure_ascii=False)[:600])
(O/"KR0070_peek_gold.txt").write_text("\n".join(L)+"\n",encoding="utf-8")
