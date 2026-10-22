# -*- coding: utf-8 -*-
import json
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = R/"data/_derived/remaining_20261022/d_census"
O = R/"data/_derived/remaining_20261022/e19_latest_comparative"
b = json.loads((D/"d5_buckets.json").read_text(encoding="utf-8"))
L=[]
for x in b:
    if x.get("code")=="KR0083":
        L.append("== "+x["q"]+" keys "+str(list(x.keys())))
        for k,v in x.items():
            if k=="its":
                for i,iv in v.items(): L.append(f"  it{i}: {json.dumps(iv,ensure_ascii=False)}")
            else:
                L.append(f"  {k}: {json.dumps(v,ensure_ascii=False)[:1500]}")
d9 = json.loads((D/"d9_disposition.json").read_text(encoding="utf-8"))
L.append("D9 type "+type(d9).__name__)
items = d9 if isinstance(d9,list) else list(d9.values())
for x in items:
    if isinstance(x,dict) and x.get("code")=="KR0083":
        L.append("D9 "+json.dumps(x,ensure_ascii=False)[:2500])
c = json.loads((D/"cand_pl_cells.json").read_text(encoding="utf-8"))
L.append("CAND "+type(c).__name__+" "+(str(list(c.keys())[:5]) if isinstance(c,dict) else str(len(c))))
cc = c if isinstance(c,list) else c.get("cells",c)
for x in (cc if isinstance(cc,list) else []):
    if "KR0083" in json.dumps(x,ensure_ascii=False):
        L.append("C "+json.dumps(x,ensure_ascii=False))
(O/"KR0083_d5_view.txt").write_text("\n".join(L)+"\n",encoding="utf-8")
