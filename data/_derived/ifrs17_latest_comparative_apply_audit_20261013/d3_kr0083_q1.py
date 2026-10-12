import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pl import *
here = os.path.dirname(os.path.abspath(__file__))
out = open(here + "/d3_kr0083_q1.txt", "w", encoding="utf-8")
for code, fyq in (("KR0083", "FY2024_Q1"), ("KR0005", "FY2024_Q1")):
    for p in find_xml(code, fyq):
        for t in load_tables(p):
            if is_statement(t):
                rows = stmt_rows(t)
                out.write(f"== {code} {fyq} table {t['idx']} line {t['line']} cap={t['caption'][:60]!r}\n")
                for it in (1, 17, 18, 19, 20, 21):
                    out.write(f"   item{it}: {define(rows, it)}\n")
