# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
txt=load(R+"/data/dart/FY2024_Q3/raw/KR0003_롯데손해보험/20241114002408.xml")
n=0
for T in tables(txt):
    if T["rows"] and any(r and r[0]["t"].startswith("Ⅰ") and "보험손익" in r[0]["t"] for r in T["rows"]):
        print("TABLE",T["line"],"pre",T["pre"][-80:])
        for r in T["rows"][:4]: print([ (c["t"][:25],(c["ctx"] or "")[:40]) for c in r])
        for r in T["rows"]:
            if r and r[0]["t"][:2] in ("Ⅰ.","Ⅱ.","Ⅲ.","Ⅳ.","Ⅴ.","Ⅵ.","Ⅶ.","Ⅷ.","Ⅸ.","Ⅹ."): print(r[0]["t"],[c["t"] for c in r[1:]])
        n+=1
        if n>=2: break
