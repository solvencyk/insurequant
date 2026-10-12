import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_pl import *
here = os.path.dirname(os.path.abspath(__file__))
out = open(here + "/d2_q1_peek.txt", "w", encoding="utf-8")
for code in ("KR0005", "KR0083"):
    ps = find_xml(code, "FY2023_Q1")
    out.write(f"== {code} {ps}\n")
    for p in ps:
        for t in load_tables(p):
            if is_statement(t):
                rows = stmt_rows(t)
                out.write(f" table {t['idx']} line {t['line']}\n")
                for lab, vals, raw in rows:
                    if re.search(r"금융수익|금융비용|투자손익|투자영업|영업이익|보험손익|보험서비스결과", lab): out.write(f"    {raw[:40]!r}: {vals}\n")
                break
