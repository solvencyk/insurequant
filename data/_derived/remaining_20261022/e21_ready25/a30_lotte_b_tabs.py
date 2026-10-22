"""a30: list the 롯데 layout-(b) single-column CSM tables of FY2025_Q2 (READ-ONLY)"""
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
    if "기초보험계약부채(자산)" in labs:
        blob = " | ".join(W.clean(c["text"]) for r in rows[:14] for c in r["cells"] if c["text"])[:300]
        op = [W.numeric_cells(r) for r in rows if nl(W.label_of(r)) == "기초보험계약부채(자산)"]
        cl = [W.numeric_cells(r) for r in rows if nl(W.label_of(r)) == "기말보험계약부채(자산)"]
        print("TABLE", t["start"], t["end"], "rows", len(rows), "open", [x[0][2] for x in op if x], "close", [x[0][2] for x in cl if x])
        print("    head:", blob)
