"""a41: KB 2023.1Q original filing: 보험손익 / 투자손익 / 당기순이익 rows in the consolidated vs separate sections (READ-ONLY)"""
import re, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W
import e21_t2 as T
sys.stdout.reconfigure(encoding="utf-8")
M = T.M
code, fy = sys.argv[1], sys.argv[2]
labs_want = sys.argv[3].split(",")
path = T.main_path(code, fy)
lines = M.read_lines(path)
print("#####", code, fy, path.name)
for t in M.iter_tables(lines):
    rows = W.rows_full(lines, t["start"], t["end"])
    for r in rows:
        lab = re.sub(r"\s+", "", W.label_of(r))
        lab2 = re.sub(r"^([ⅠⅡⅢⅣⅤⅥⅦ]|[IVX]+|\d+|\(\d+\))[\.\)]?", "", lab)
        if lab2 in labs_want:
            print(f"   table@L{t['start']} title={t['title'][:14]!r} R{r['tr_line']} {W.label_of(r)[:14]!r}", [(c['text'], c['line']) for c in r['cells'][1:7]])
