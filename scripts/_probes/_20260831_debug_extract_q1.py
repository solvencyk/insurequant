# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_disclosure_parser import (
    extract_kics_detail_rows, build_label_lookups,
    extract_kics_summary_overview_rows, extract_kics_detail_section,
)

md = (REPO / "md_inbox/FY2023_Q1/KR0029_AIG손해보험.md").read_text(encoding="utf-8")
quarter = "2023.1Q"

sov = extract_kics_summary_overview_rows(md, quarter)
print(f"summary_overview_rows: {len(sov)}")
for l, v in sov:
    print("  SOV", repr(l), repr(v))

section = extract_kics_detail_section(md)
print(f"detail_section found: {section is not None}, len={len(section) if section else 0}")
if section:
    print("section head (first 300 chars):", repr(section[:300]))

pairs = extract_kics_detail_rows(md, quarter)
print(f"\nFINAL pairs: {len(pairs)}")
for l, v in pairs:
    print("  PAIR", repr(l), repr(v))
