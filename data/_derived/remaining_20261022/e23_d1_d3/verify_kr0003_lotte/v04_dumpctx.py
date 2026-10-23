# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
which=sys.argv[1]  # new|orig
txt=load({"new":NEW,"orig":ORIG}[which])
col="PFY2023" if which=="new" else "CFY2023"
out=[]
for T in tables(txt):
    for row in T["rows"]:
        lab=row[0]["t"] if row else ""
        for c in row[1:]:
            if c["ctx"] and c["ctx"].startswith(col+"d") and "SeparateMember" in c["ctx"]:
                out.append((c["line"],T["line"],lab,c["t"],c["ctx"][:50]))
for o in out: print("\t".join(str(x) for x in o))
