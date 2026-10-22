# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
g = json.loads((ROOT/"data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
L=[]
for k in ("null_dangi","set_dangi"):
    d = g[k]
    L.append(k+" keys "+str(list(d.keys())))
    for kk,v in d.items():
        if kk=="cells":
            L.append(f"  cells n={len(v)}; first 3 {v[:3]}; last 2 {v[-2:]}")
        else:
            L.append(f"  {kk}: {str(v)[:1500]}")
L.append("set _doc: "+str(g.get("_doc"))[:1500])
L.append("set n="+str(len(g["set"])))
kyo=[e for e in g["set"] if e["원보험사코드"]=="KR0073"]
L.append("kyobo set n="+str(len(kyo))+" example "+json.dumps(kyo[-1],ensure_ascii=False)[:1200])
(ROOT/"data/_derived/remaining_20261022/e19_latest_comparative/KR0083_peek_gold.txt").write_text("\n".join(L)+"\n",encoding="utf-8")
