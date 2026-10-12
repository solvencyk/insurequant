import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pl import *
here = os.path.dirname(os.path.abspath(__file__))
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(here + "/l2_db_q3.txt", "w", encoding="utf-8")
code = "KR0011"
for fyq, q, cq in (("FY2024_Q3", "2023.3Q", "2024.3Q"), ("FY2024_Q2", "2023.2Q", "2024.2Q"), ("FY2024_Q1", "2023.1Q", "2024.1Q")):
    p = find_xml(code, fyq)[0]
    best = None
    for t in load_tables(p):
        if not is_statement(t): continue
        rows = stmt_rows(t); v = define_all(rows, 25)
        if v and len(v) >= 4 and abs(v[-3] / 1e6 - float(master[(code, cq, 25)]["값"])) < 0.01 if (code, cq, 25) in master and master[(code, cq, 25)].get("값") not in (None, "") else False:
            best = (t, rows); break
    if not best: out.write(f"{fyq}: no anchored statement table for item 25 (cur master {master.get((code,cq,25),{}).get('값')})\n"); continue
    t, rows = best
    for it in (1, 17, 18, 19, 20, 24, 25, 26, 27, 28, 29, 30, 31, 32):
        v = define_all(rows, it)
        mv = master.get((code, q, it), {}).get("값")
        out.write(f"{q} item{it}: printed prior cum = {v[-1]/1e6 if v else None}  master now = {mv}\n")
