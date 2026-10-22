"""a37: 영업외 rows of the 한화 FY2023_Q2 original filing around the income statement (READ-ONLY)"""
import re, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_plan as PL
import e21_raw as W
import e21_t2 as T
sys.stdout.reconfigure(encoding="utf-8")
M = T.M
path = T.main_path("KR0068", "FY2023_Q2")
lines = M.read_lines(path)
for t in M.iter_tables(lines):
    if not (62000 <= t["start"] <= 62700):
        continue
    rows = W.rows_full(lines, t["start"], t["end"])
    labs = [W.label_of(r) for r in rows]
    if any("영업외" in x for x in labs):
        print("TABLE", t["start"], t["end"], "caption", t["caption"][:50])
        for r in rows:
            lab = W.label_of(r)
            if re.search(r"영업외|영업이익|법인세차감전|세전", lab.replace(" ", "")) or lab.replace(" ", "").startswith(("Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ")):
                print("   R", r["tr_line"], lab[:30], [(c["text"], c["line"]) for c in r["cells"][1:9]])
