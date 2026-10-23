# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
txt=load(NEW); Ts=tables(txt)
lo,hi=int(sys.argv[1]),int(sys.argv[2])
for T in Ts:
    last=T["rows"][-1][-1]["line"] if T["rows"] and T["rows"][-1] else T["line"]
    if T["line"]<=hi and last>=lo:
        print("### TABLE",T["line"],"..",last,"pre:",T["pre"][-120:])
        for row in T["rows"]:
            if row: print(row[0]["line"],"|"," | ".join(c["t"] for c in row))
