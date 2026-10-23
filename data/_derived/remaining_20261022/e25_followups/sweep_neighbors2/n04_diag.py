# -*- coding: utf-8 -*-
import sys
sys.argv = [sys.argv[0]] + ["__none__"] + sys.argv[1:]   # n00_lib reads ONLY from argv[1:]; the first extra arg is a dummy filter so no targets are built
from n00_lib import *
code, q = sys.argv[2], sys.argv[3]
fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
mq = f"{int(q[:4]) + 1}.{q[5:]}"
path = T.main_path(code, fy)
lines, bl = blocks_of(path)
print(path.name, "blocks", len(bl))
print("master q+4:", {i: pl.get((code, i, mq)) for i in sorted(ITEMS, key=int)}, " master q:", {i: pl.get((code, i, q)) for i in sorted(ITEMS, key=int)})
for b in bl:
    print(f"--- block@L{b['start']} unit={b['unit']} cap={b['cap'][:50]!r} hdr={b['hdr'][:70]!r}")
    for t, v in b["terms"].items():
        print("    ", t, v["label"][:45], "n=", v["n"], [x[0] for x in v["nums"]][:16])
