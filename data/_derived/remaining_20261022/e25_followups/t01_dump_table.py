# -*- coding: utf-8 -*-
"""READ-ONLY: dump the XML table(s) that contain (or start within N lines after) a given 1-based physical line of a DART xml.
usage: t01_dump_table.py PATH LINE [AFTER_LINES=0] [MAXCELLS=12]
prints for every table whose [start, end] intersects [LINE, LINE+AFTER]: title, caption, unit guess, then each row: tr_line | label | numeric cells with (line)"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W  # noqa: E402
import e21_t2 as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
M = T.M
path, line = sys.argv[1], int(sys.argv[2])
after = int(sys.argv[3]) if len(sys.argv) > 3 else 0
maxc = int(sys.argv[4]) if len(sys.argv) > 4 else 12
lines = M.read_lines(path)
for t in M.iter_tables(lines):
    if t["end"] < line or t["start"] > line + after:
        continue
    unit = T.find_unit(lines, t, span=2500)
    print(f"=== table lines {t['start']}-{t['end']} title={t['title']!r} caption={t['caption']!r} unit={unit}")
    for r in W.rows_full23(lines, t["start"], t["end"]) if hasattr(W, "rows_full23") else W.rows_full(lines, t["start"], t["end"]):
        cells = [(c["text"], c["line"]) for c in r["cells"]]
        lab = cells[0][0] if cells else ""
        rest = " | ".join(f"{tx}@{ln}" for tx, ln in cells[1:1 + maxc])
        print(f"  R{r['tr_line']}: {lab[:46]!r} :: {rest}")
