# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
txt=load(ORIG)
for T in tables(txt):
    if T["line"] in (26619,):
        for r in T["rows"]:
            if r: print(r[0]["line"],"|"," | ".join(c["t"] for c in r))
