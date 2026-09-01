# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import fill_period_to_disclosure as F
from solvency.parser.kics_disclosure_parser import extract_kics_detail_rows

md_path = F.MD_INBOX / "FY2023_Q1" / "KR0049_악사손해보험.md"
table = extract_kics_detail_rows(md_path.read_text(encoding="utf-8"), "2023.1Q")
for label, raw in table:
    if "비례성" in label:
        idx = label.find("요구")
        segment = label[idx:idx+8]
        print(f"label repr: {label!r}")
        print(f"segment: {segment!r}")
        for ch in segment:
            print(f"  {ch!r} U+{ord(ch):04X}")
