# -*- coding: utf-8 -*-
"""READ-ONLY pass3 d12: print every table whose start line lies in [LO, HI] of a filing (rows with non-empty cells, physical xml line numbers).
usage: d12_dump_range.py CODE FYxxxx_Qn LO HI [maxrows]"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
code, fy, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
maxrows = int(sys.argv[5]) if len(sys.argv) > 5 else 60
path = P.main_path(code, fy)
lines = P.M.read_lines(path)
print(f"##### {code} {fy} {P.M.rel(path)} tables starting in L{lo}-L{hi}")
for t in P.M.iter_tables(lines):
    if not (lo <= t["start"] <= hi):
        continue
    rows = P.E.rows_full23(lines, t["start"], t["end"])
    unit = P.T.find_unit(lines, t, span=2500)
    print(f"--- table@L{t['start']}-{t['end']} unit={unit} rows={len(rows)} title={t['title']!r}")
    n = 0
    for r in rows:
        if not r["cells"]:
            continue
        txt = " | ".join(f"{c['text']}@{c['line']}" for c in r["cells"][:10] if c["text"].strip())
        if txt.strip():
            print(f"   R{r['tr_line']:>6} {txt[:260]}")
            n += 1
            if n >= maxrows:
                print("   ...")
                break
