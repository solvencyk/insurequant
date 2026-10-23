# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
for f in ["PL_breakdown.json","CSM_waterfall.json","PL_breakdown_provenance.json","CSM_waterfall_provenance.json"]:
    d=json.load(open(R+f,encoding="utf-8"))
    print(f,type(d).__name__,len(d))
    if isinstance(d,list):
        r=[x for x in d if x.get("원보험사코드")=="KR0099"][:2]
        print(json.dumps(r,ensure_ascii=False)[:1200])
    else:
        ks=list(d)[:5]; print(ks)
        for k in ks[:2]:
            print(k, json.dumps(d[k],ensure_ascii=False)[:600])
