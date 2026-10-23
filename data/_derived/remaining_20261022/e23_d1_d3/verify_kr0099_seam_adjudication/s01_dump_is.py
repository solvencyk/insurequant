# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_seam_adjudication/"
for q in ("2023.3Q","2023.4Q","2024.3Q","2024.4Q"):
    tb=tables(load(XML[q]))
    c=[(i,t) for i,t in enumerate(tb) if "4-2. 포괄손익계산서" in t["pre"][-260:] and len(t["rows"])>30]
    print("=====",q,[ (i,t["line"],len(t["rows"])) for i,t in c])
    i,t=c[0]
    with open(OUT+"s01_is_%s.txt"%q,"w",encoding="utf-8") as f:
        for r in t["rows"]:
            f.write(" | ".join(x for x,_ in r)+"\n")
    for r in t["rows"][:60]:
        print(" | ".join(x for x,_ in r))
