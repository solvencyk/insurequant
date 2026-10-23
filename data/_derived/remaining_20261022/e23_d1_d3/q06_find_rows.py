# -*- coding: utf-8 -*-
"""e23 probe (read-only): list the tables of a DART filing that contain a row whose normalised label matches a regex, with caption, header text and the matching rows' cells (physical lines).
usage: q06_find_rows.py <code> <FYxxxx_Qn> <label regex on whitespace-free text> [max tables] [--file name]"""
import re
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W  # noqa: E402
import e21_t2 as T  # noqa: E402

M = T.M
sys.stdout.reconfigure(encoding="utf-8")
code, fy, pat = sys.argv[1], sys.argv[2], sys.argv[3]
mx = int(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else 12
which = None
if "--file" in sys.argv:
    which = sys.argv[sys.argv.index("--file") + 1]
paths = [p for p in M.main_xmls(code, fy) if (which is None or p.name == which)]
rx = re.compile(pat)
for path in paths:
    lines = M.read_lines(path)
    s0 = T.sep_notes_from(lines)
    print("#" * 100)
    print(M.rel(path), "lines", len(lines), "separate notes start", s0)
    n = 0
    for t in M.iter_tables(lines):
        rows = W.rows_full(lines, t["start"], t["end"])
        hit = [r for r in rows if rx.search(T.nl(W.label_of(r)))]
        if not hit:
            continue
        n += 1
        if n > mx:
            print(f"... more tables (max {mx})")
            break
        hdr = " | ".join(" ".join(c["text"] for c in r["cells"]) for r in rows[:3])
        print(f"--- table L{t['start']}-{t['end']} sep={'Y' if t['start'] >= s0 else 'N'} caption={t['caption'][:90]!r} title={t['title'][:40]!r}")
        print(f"    header: {hdr[:260]}")
        for r in hit[:6]:
            print(f"    row L{r['tr_line']} {W.label_of(r)[:50]!r}: " + " ; ".join(f"{c['text']}@{c['line']}" for c in r["cells"] if c["text"] != W.label_of(r))[:420])
