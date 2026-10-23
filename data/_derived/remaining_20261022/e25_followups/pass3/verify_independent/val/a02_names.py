# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json", encoding="utf-8"))
n = {}
for r in d:
    n[r["항목번호"]] = r["항목명"]
for k in sorted(n, key=str): print(k, n[k])
for c, q in [("KR0070","2025.2Q"),("KR0070","2025.3Q"),("KR0070","2026.2Q"),("KR0070","2025.1Q")]:
    print(c,q,{r["항목번호"]:(r.get("값"),r.get("값_당분기")) for r in d if r["원보험사코드"]==c and r["공시분기"]==q and str(r["항목번호"]).isdigit() and int(r["항목번호"])<=12})
