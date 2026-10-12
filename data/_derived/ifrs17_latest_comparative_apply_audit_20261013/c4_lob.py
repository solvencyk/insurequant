import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_tier2 import *
here = os.path.dirname(os.path.abspath(__file__))
code = sys.argv[1]
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(here + f"/c4_lob_{code}.txt", "w", encoding="utf-8")
for fyq, rc in [("FY2024_Q1", None), ("FY2024_Q2", None), ("FY2024_Q3", None)]:
    p = find_xml(code, fyq)[0]
    ty = pairs(note_tables(p))
    # second section (last 4 types)
    sec = ty[-4:]
    out.write(f"== {fyq} types {[(t[0]['idx'], t[1]['idx'] if t[1] else None) for t in sec]}\n")
    for which, lab in ((0, "cur"), (1, "prior")):
        def tot(ti, occ, col): return sec[ti][which]["rows"].get(("합계", occ), {}).get(col)
        for col in ("장기", "자동차", "일반"):
            try:
                v = tot(2, 1, col) - tot(3, 1, col) - tot(2, 2, col) + tot(3, 2, col)
            except Exception as e:
                v = None
            out.write(f"   {lab} {col}: REV {tot(2,1,col)} COST {tot(3,1,col)} REcost {tot(2,2,col)} RErev {tot(3,2,col)} -> LOB profit {v}\n")
    q = {"FY2024_Q1": "2024.1Q", "FY2024_Q2": "2024.2Q", "FY2024_Q3": "2024.3Q"}[fyq]
    out.write(f"   master {q}: i13={master.get((code,q,13),{}).get('값')} i14={master.get((code,q,14),{}).get('값')} i2={master.get((code,q,2),{}).get('값')}\n")
