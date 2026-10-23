# -*- coding: utf-8 -*-
"""e23 probe (read-only): dump one table (by any physical line inside it) of a DART xml with all rows / cells / lines.
usage: q08_dump_table.py <relative xml path under repo> <line> [maxrows] [--cells N]"""
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W  # noqa: E402
import e21_t2 as T  # noqa: E402

M = T.M
sys.stdout.reconfigure(encoding="utf-8")
rel, ln = sys.argv[1], int(sys.argv[2])
mx = int(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 80
ncell = int(sys.argv[sys.argv.index("--cells") + 1]) if "--cells" in sys.argv else 12
path = M.ROOT / rel
lines = M.read_lines(path)
for t in M.iter_tables(lines):
    if t["start"] <= ln <= t["end"]:
        print(f"table L{t['start']}-{t['end']} caption={t['caption'][:120]!r} title={t['title'][:50]!r}")
        print("unit:", T.find_unit(lines, t, span=2500) if True else "")
        rows = W.rows_full(lines, t["start"], t["end"])
        for k, r in enumerate(rows[:mx]):
            cells = [f"{c['text'][:34]}@{c['line']}" for c in r["cells"][:ncell]]
            print(f"{k:3d} TR{r['tr_line']}: " + " | ".join(cells))
        break
else:
    print("no table contains that line")
