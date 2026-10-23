import sys
sys.argv = [sys.argv[0], "__lib__"]
from n00_lib import *
path = T.main_path("KR0082", "FY2024_Q1")
lines, s0, tabs = s2lib.tables_sep2(path)
for t, rows in tabs:
    cap = E.nl(t["caption"] or "")
    if "발행한보험계약의보험수익" in cap:
        print(t["start"], cap[:60], len(rows))
        for r in rows[:5]:
            print("  ", [c["text"] for c in r["cells"]], split_row(r)[0], len(split_row(r)[1]))
