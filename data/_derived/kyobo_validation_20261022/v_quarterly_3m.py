# -*- coding: utf-8 -*-
"""Compare master 값_당분기 (single quarter, = YTD delta) of Kyobo PL with the 3-month column printed in the latest comparative filing."""
import sys, json
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
import importlib.util
from vreader import *
from vfiles import main_xml
spec = importlib.util.spec_from_file_location("rp", "data/_derived/kyobo_validation_20261022/v_reread_pl.py")
src = open("data/_derived/kyobo_validation_20261022/v_reread_pl.py", encoding="utf-8").read().replace("\nmain()\n", "\n")
ns = {}; exec(compile(src, "rp", "exec"), ns)
pl = json.load(open("PL_breakdown.json", encoding="utf-8"))
M = {(r["공시분기"], int(r["항목번호"])): r["값_당분기"] for r in pl if r["원수사명"] == "교보생명보험" and str(r["항목번호"]).isdigit()}
# (quarter, filing with prior-year 3M column idx=2)
for q, fy in (("2023.2Q", "FY2024_Q2"), ("2023.3Q", "FY2024_Q3"), ("2024.2Q", "FY2025_Q2"), ("2024.3Q", "FY2025_Q3")):
    f, tl, hdr, out = ns["derive"](fy, 2)
    print("==", q, "published 3M (prior-year column) vs master 값_당분기 (백만원)")
    for it in (1, 17, 19, 20, 22, 23, 24, 25, 31):
        v = out[it][0]; m = M.get((q, it))
        print(f"   item{it:>2} pub3M={v:>16,.1f} master_qtr={m:>16,.1f} diff={m - v:>+14,.1f}")
