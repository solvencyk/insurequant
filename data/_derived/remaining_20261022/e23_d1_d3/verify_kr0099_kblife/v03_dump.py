# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
q=sys.argv[1]; lo=int(sys.argv[2]); hi=int(sys.argv[3])
txt=load(XML[q]); tb=tables(txt)
for i,t in enumerate(tb):
    if lo<=t["line"]<=hi:
        print("=== TABLE",i,"line",t["line"],"pre:",t["pre"][-150:])
        for r in t["rows"]: print(" | ".join(f"{c}" + (f"[x{s}]" if s>1 else "") for c,s in r))
