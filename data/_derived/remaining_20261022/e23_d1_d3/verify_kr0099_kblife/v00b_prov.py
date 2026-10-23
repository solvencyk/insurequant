# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
for f in ["PL_breakdown_provenance.json","CSM_waterfall_provenance.json"]:
    d=json.load(open(R+f,encoding="utf-8"))
    for k,v in d.items():
        s=json.dumps(v,ensure_ascii=False)
        print(f,k,type(v).__name__,len(s), s[:200] if len(s)<3000 else "")
    # find KR0099
    s=json.dumps(d,ensure_ascii=False)
    print(f, "KR0099 count", s.count("KR0099"))
