import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pl import *
here = os.path.dirname(os.path.abspath(__file__))
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open(here + "/l3_db_q3b.txt", "w", encoding="utf-8")
p = find_xml("KR0011", "FY2024_Q3")[0]
for t in load_tables(p):
    if not is_statement(t): continue
    rows = stmt_rows(t)
    v25 = define_all(rows, 25)
    if not v25: continue
    out.write(f"table {t['idx']} line {t['line']} cols {len(v25)} cap {t['caption'][:60]!r}\n")
    for it in (1, 17, 24, 25, 26, 27, 28, 29, 30, 31, 32):
        v = define_all(rows, it)
        out.write(f"   item{it}: cur cum {v[-3]/1e6 if v and len(v)>=4 else None}  prior cum {v[-1]/1e6 if v else None} | master 2024.3Q {master.get(('KR0011','2024.3Q',it),{}).get('값')} 2023.3Q {master.get(('KR0011','2023.3Q',it),{}).get('값')}\n")
