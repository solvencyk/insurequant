"""a31: list the 미래에셋 product CSM roll-forward tables of FY2025_Q1 (READ-ONLY)"""
import re, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W
import e21_t2 as T
M = T.M; nl = T.nl
sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
path = T.main_path(code, fy); lines = M.read_lines(path); s0 = T.sep_notes_from(lines)
print(path.name, "sep notes from", s0)
for t in M.iter_tables(lines):
    if t["start"] < s0: continue
    rows = W.rows_full(lines, t["start"], t["end"])
    labs = [nl(W.label_of(r)) for r in rows]
    if any(x == "기초잔액" for x in labs) and any(x == "기말잔액" for x in labs):
        hdr = nl(" ".join(c["text"] for r in rows[:6] for c in r["cells"]))
        # CSM subtotal of the first 기초 잔액 row
        op = [W.numeric_cells(r, 1) for r in rows if nl(W.label_of(r)) == "기초잔액"]
        print("TABLE", t["start"], t["end"], "caption", repr(t["caption"][:30]), "rows", len(rows), "hdr-has-재보험", "재보험" in hdr, "opening rows (cur,prior) CSM소계:",
              [x[-2][2] if len(x) >= 2 else x for x in op])
