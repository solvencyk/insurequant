# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")
from pathlib import Path
from solvency.parser.kics_disclosure_parser import extract_kics_detail_rows, build_label_lookups
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero

MD = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\md_inbox\FY2026_Q2\KR0069_삼성생명.md")
md_text = MD.read_text(encoding="utf-8")
table = extract_kics_detail_rows(md_text, "2026.2Q")
print(f"n pairs extracted: {len(table)}")
for label, val in table:
    print(f"  {label!r:60s} = {val}")

# Now try matching against 2026.1Q baseline item names for this company
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
baseline = [r for r in rows if r["원보험사코드"] == "KR0069" and r["공시분기"] == "2026.1Q" and str(r["항목번호"]).isdigit() and int(r["항목번호"]) <= 28]
lookup, core = build_label_lookups(table)
print(f"\n=== matched against {len(baseline)} baseline (2026.1Q) items 1-28 ===")
for b in sorted(baseline, key=lambda r: int(r["항목번호"])):
    v = match_baseline_value_or_zero(b["항목명"], lookup, core, table)
    print(f"  item{b['항목번호']:>3} {b['항목명']!r:45s} -> {v}")
