# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0003_lotte")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
txt=load(ORIG)
for T in tables(txt):
    labs=[re.sub(r"\s+","",r[0]["t"]) for r in T["rows"] if r]
    if "보험계약마진상각액" in labs and "기초순보험계약부채" in labs:
        print("TABLE",T["line"],"pre",T["pre"][-60:])
        for r in T["rows"][:6]: print("   ",[c["t"][:14] for c in r])
        for r in T["rows"]:
            if r and re.sub(r"\s+","",r[0]["t"]) in ("기초순보험계약부채","최초인식계약","보험금융손익","보험계약마진을조정하는추정치의변동","보험계약마진상각액","기말순보험계약부채"): print("   ",r[0]["line"],[c["t"] for c in r])
