import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
import openpyxl
wb = openpyxl.load_workbook(Path(sys.argv[1]), data_only=True, read_only=True)
sn, r0, r1 = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
ws = wb[sn]
for i, row in enumerate(ws.iter_rows(min_row=r0, max_row=r1, values_only=True), r0):
    cells = ["" if c is None else (f"{c:,.1f}" if isinstance(c, float) else str(c))[:18] for c in row[:18]]
    if any(c for c in cells):
        print(f"r{i:3d}", " | ".join(cells))
