# -*- coding: utf-8 -*-
import json, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
def head(rel): return json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
for rel in ["PL_breakdown.json","CSM_waterfall.json"]:
    l=json.load(open(R+"/"+rel,encoding="utf-8")); h=head(rel)
    print("==",rel, "fields:", sorted(l[0]))
    for q in ("2023.3Q","2023.4Q","2024.1Q"):
        print("-- quarter",q)
        hm={(r["항목번호"]):r for r in h if r["원보험사코드"]=="KR0003" and r["공시분기"]==q}
        for r in sorted((r for r in l if r["원보험사코드"]=="KR0003" and r["공시분기"]==q),key=lambda r:r["항목번호"]):
            o=hm.get(r["항목번호"],{})
            print(r["항목번호"],r.get("항목명") or r.get("항목"),"| 값",r.get("값"),"| 당분기",r.get("값_당분기"),"| HEAD값",o.get("값"),"HEAD당분기",o.get("값_당분기"))
