"""a38: every table of the 한화 FY2023_Q2 original filing that has a 영업외수익 row (READ-ONLY)"""
import re, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W
import e21_t2 as T
sys.stdout.reconfigure(encoding="utf-8")
M = T.M
path = T.main_path("KR0068", "FY2023_Q2")
lines = M.read_lines(path)
s0 = T.sep_notes_from(lines)
print(path.name, "sep notes from", s0, "n lines", len(lines))
for t in M.iter_tables(lines):
    rows = W.rows_full(lines, t["start"], t["end"])
    labs = [re.sub(r"\s+", "", W.label_of(r)) for r in rows]
    if any(x.endswith("영업외수익") for x in labs):
        print("TABLE", t["start"], t["end"], "title", t["title"][:30], "| caption", t["caption"][:60])
        for r in rows:
            lab = re.sub(r"\s+", "", W.label_of(r))
            if lab.endswith(("영업외수익", "영업외비용", "영업이익")):
                print("   R", r["tr_line"], W.label_of(r)[:24], [(c["text"], c["line"]) for c in r["cells"][1:9]])
