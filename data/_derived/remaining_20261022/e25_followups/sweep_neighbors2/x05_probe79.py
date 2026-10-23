import sys
sys.argv = [sys.argv[0], "__lib__"]
from n00_lib import *
fy, start = "FY2025_Q2", 89911
path = T.main_path("KR0079", fy)
lines, s0, tabs = s2lib.tables_sep2(path)
for t, rows in tabs:
    if t["start"] != start: continue
    for r in rows:
        lab, nums = split_row(r)
        if "서비스의이전" in lab or "위험조정변동분" in lab or "보험계약마진을조정" in lab:
            v = [round(x[0] / 1e6, 1) for x in nums]
            print(lab[:40], len(v), v)
            print("   sum all", round(sum(v), 1))
    hdr = [[c["text"][:16] for c in r["cells"]] for r in rows[:9]]
    for h in hdr: print("H", h[:30])
print("master 2025.2Q 4/5:", pl.get(("KR0079", "4", "2025.2Q")), pl.get(("KR0079", "5", "2025.2Q")))
