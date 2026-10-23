# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
pl = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json", encoding="utf-8"))
qs = sorted({r["공시분기"] for r in pl if r["원보험사코드"]=="KR0087"})
for q in qs:
    row = {}
    for r in pl:
        if r["원보험사코드"]=="KR0087" and r["공시분기"]==q and str(r["항목번호"]) in ("3","4","5","6","7","8","9","10","11","12"):
            row[str(r["항목번호"])] = (r.get("값"), r.get("값_당분기"))
    print(q, {k: row.get(k) for k in ("8","9","10","11","12")})
