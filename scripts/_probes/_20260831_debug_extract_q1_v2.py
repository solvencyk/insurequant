# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_disclosure_parser import (
    extract_kics_detail_section, _iter_section_tables,
    make_quarter_column_picker, _looks_like_kics_row,
)

md = (REPO / "md_inbox/FY2023_Q1/KR0029_AIG손해보험.md").read_text(encoding="utf-8")
quarter = "2023.1Q"
pick_col = make_quarter_column_picker(quarter)

section = extract_kics_detail_section(md)
tables = _iter_section_tables(section)
print(f"num tables in section: {len(tables)}")
for ti, tbl in enumerate(tables):
    if not tbl:
        print(f"table {ti}: EMPTY")
        continue
    header = tbl[0]
    h_idx = pick_col(header)
    print(f"table {ti}: rows={len(tbl)} header={header!r} pick_col(header)={h_idx}")
    if len(tbl) > 1:
        row1 = tbl[1]
        h_idx2 = pick_col(row1)
        print(f"    row1={row1!r} pick_col(row1)={h_idx2}")
    print(f"    _looks_like_kics_row(header[0])={_looks_like_kics_row(header[0])}")
