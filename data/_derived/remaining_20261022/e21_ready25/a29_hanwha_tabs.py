"""a29: list the candidate prior CSM roll-forward tables of 한화 FY2024_Q1 (READ-ONLY)"""
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
    if not re.match(r"^2\)\s*(전분기|전반기|전기)", t["caption"] or ""): continue
    rows = W.rows_full(lines, t["start"], t["end"])
    labs = [nl(W.label_of(r)) for r in rows]
    if any("최초인식한계약의효과" in x for x in labs):
        print("TABLE", t["start"], t["end"], "caption", t["caption"][:30], "| prev P caption line", t["caption_line"], "| first labels", labs[:3], "| n rows", len(rows))
        print("   title:", t["title"][:60])
