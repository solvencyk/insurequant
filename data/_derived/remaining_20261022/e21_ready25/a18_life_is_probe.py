"""a18_life_is_probe: print the insurance-related rows of the SEPARATE statement of each life bucket's later filing (prior cumulative cell text) -- label design for the life IS readers (READ-ONLY)"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R
sys.stdout.reconfigure(encoding="utf-8")
BUCKETS = [("KR0104", "FY2024_Q1"), ("KR0104", "FY2024_Q2"), ("KR0083", "FY2025_Q4"), ("KR0079", "FY2024_Q4"), ("KR0079", "FY2025_Q1"), ("KR0079", "FY2025_Q2"), ("KR0079", "FY2025_Q3"),
           ("KR0068", "FY2024_Q1"), ("KR0068", "FY2024_Q2"), ("KR0068", "FY2024_Q3"), ("KR0099", "FY2024_Q1"), ("KR0070", "FY2025_Q4")]
only = sys.argv[1:]
for code, fy in BUCKETS:
    if only and f"{code}_{fy}" not in only:
        continue
    st = R.Stmt(code, fy)
    print("#####", code, fy, st.fmt, st.unit, st.rel, "rows", len(st.rows))
    for r in st.rows:
        if r.oci:
            break
        if "보험" in r.lab or r.lab.startswith(("영업", "사업", "투자", "수익", "비용", "기타")):
            cur = st.pick_cell(r, "cur", "cum")
            pri = st.pick_cell(r, "prior", "cum")
            n_cells = len([c for c in r.cells if c["text"] != ""])
            print(f"  L{r.line} {r.raw.strip()[:50]!r} -> {r.lab[:30]!r} | prior-cum={None if pri is None else (pri['text'], pri['line'])} cur-cum={None if cur is None else (cur['text'], cur['line'])} ncells={n_cells}")
