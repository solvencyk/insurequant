# -*- coding: utf-8 -*-
"""Cell-level diff of two xlsx (read-only, data_only). Prints per-sheet changed cells, grouped by (code, quarter)."""
import sys
from collections import Counter
from openpyxl import load_workbook

a_path, b_path = sys.argv[1], sys.argv[2]
a = load_workbook(a_path, read_only=True, data_only=True)
b = load_workbook(b_path, read_only=True, data_only=True)
print("sheets equal:", a.sheetnames == b.sheetnames, len(a.sheetnames))
for name in a.sheetnames:
    ra = [list(r) for r in a[name].iter_rows(values_only=True)]
    rb = [list(r) for r in b[name].iter_rows(values_only=True)]
    if len(ra) != len(rb):
        print(f"{name}: ROW COUNT {len(ra)} -> {len(rb)}")
    n = 0
    codes = Counter()
    qtrs = Counter()
    for i, (x, y) in enumerate(zip(ra, rb)):
        if x != y:
            diffcols = [j for j in range(max(len(x), len(y))) if (x[j] if j < len(x) else None) != (y[j] if j < len(y) else None)]
            n += len(diffcols)
            codes[y[0]] += len(diffcols)
            qtrs[y[6] if len(y) > 6 else None] += len(diffcols)
    if n:
        print(f"{name}: changed cells={n} codes={dict(codes)} quarters={dict(sorted(qtrs.items(), key=lambda t: str(t[0])))}")
    else:
        print(f"{name}: identical")
