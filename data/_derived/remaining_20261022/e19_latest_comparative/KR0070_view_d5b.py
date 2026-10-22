# -*- coding: utf-8 -*-
import json
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = R/"data/_derived/remaining_20261022/d_census"
O = R/"data/_derived/remaining_20261022/e19_latest_comparative"
b = json.loads((D/"d5_buckets.json").read_text(encoding="utf-8"))
L=[]
for x in b:
    if x.get("code")=="KR0070":
        L.append(f"== {x['q']} scope={x['scope']} div={x['div']} real={x['real']} gold_in_block={x['gold_in_block']} gold_overlap={x['gold_overlap']} fy_status={x['fy_status']} verdict1012={x['pl_verdict_1012']}")
        L.append(f"   csm={json.dumps(x['csm'],ensure_ascii=False)}")
        L.append(f"   cls={x['cls']}")
        L.append(f"   its(prior vs master) " + " ".join(f"{k}:{v['prior']}/{v['master']}" for k,v in x['its'].items()))
d9 = json.loads((D/"d9_disposition.json").read_text(encoding="utf-8"))
items = d9 if isinstance(d9,list) else list(d9.values())
for x in items:
    if isinstance(x,dict) and x.get("code")=="KR0070":
        L.append("D9 "+x.get("q","?")+" "+json.dumps({k:v for k,v in x.items() if k in ("disposition","closes","closure_basis","reasons","reason","gold")},ensure_ascii=False)[:1500])
(O/"KR0070_d5_view.txt").write_text("\n".join(L)+"\n",encoding="utf-8")
