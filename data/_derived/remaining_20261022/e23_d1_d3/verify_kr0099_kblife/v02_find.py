# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
q=sys.argv[1]; kws=sys.argv[2:]
txt=load(XML[q]); tb=tables(txt)
print(q,len(txt),"tables",len(tb))
for i,t in enumerate(tb):
    flat=" ".join(c for r in t["rows"] for c,_ in r)
    if all(k in flat for k in kws):
        print("TABLE",i,"line",t["line"],"rows",len(t["rows"]),"pre:",t["pre"][-120:])
