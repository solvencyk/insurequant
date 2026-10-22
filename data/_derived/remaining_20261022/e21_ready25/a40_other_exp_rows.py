"""a40: every row labelled 기타사업비(용) in the ORIGINAL filings of the four gold cells, with the section title and the first numeric cells (READ-ONLY)"""
import re, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W
import e21_t2 as T
sys.stdout.reconfigure(encoding="utf-8")
M = T.M
for code, fy in (("KR0010", "FY2023_Q1"), ("KR0010", "FY2023_Q2"), ("KR0001", "FY2023_Q1"), ("KR0001", "FY2023_Q2")):
    path = T.main_path(code, fy)
    lines = M.read_lines(path)
    print("#####", code, fy, path.name, "lines", len(lines))
    for t in M.iter_tables(lines):
        rows = W.rows_full(lines, t["start"], t["end"])
        for r in rows:
            lab = re.sub(r"\s+", "", W.label_of(r))
            if lab.endswith(("기타사업비용", "기타사업비")):
                print(f"   table@L{t['start']} title={t['title'][:20]!r} cap={t['caption'][:40]!r} R{r['tr_line']} {W.label_of(r)[:20]!r}", [(c['text'], c['line']) for c in r['cells'][1:9]])
