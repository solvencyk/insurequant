# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
wt = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json", encoding="utf-8"))
M = {(r["공시분기"], str(r["항목번호"])): (r.get("값"), r.get("값_당분기")) for r in wt if r["원보험사코드"]=="KR0032"}
for q in ("2023.1Q","2023.2Q","2023.3Q","2023.4Q"):
    print(q, {k: (None if M.get((q,str(k))) is None else (None if M[(q,str(k))][0] is None else round(M[(q,str(k))][0],1))) for k in [1,2,3,4,5,6,7,8,15,16,17,18,19,20,21,22]})
