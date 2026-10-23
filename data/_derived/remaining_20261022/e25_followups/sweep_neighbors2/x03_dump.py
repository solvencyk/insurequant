import sys
sys.argv = [sys.argv[0], "__lib__"] + sys.argv[1:]
from n00_lib import *
code, fy, start = sys.argv[2], sys.argv[3], int(sys.argv[4])
path = T.main_path(code, fy)
lines, s0, tabs = s2lib.tables_sep2(path)
for t, rows in tabs:
    if t["start"] in (start,):
        print(t["start"], E.nl(t["caption"] or "")[:60], len(rows))
        for r in rows: print("  ", f"L{r['tr_line']}", [c["text"][:26] for c in r["cells"]])
