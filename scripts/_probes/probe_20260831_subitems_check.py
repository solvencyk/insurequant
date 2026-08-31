# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
from pathlib import Path
import fill_subitems_to_disclosure as fs

MD_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\md_inbox\FY2026_Q2")
for code, fname in [("KR0001", "KR0001_메리츠화재해상보험.md"), ("KR1011", "KR1011_IBK연금보험.md")]:
    text = (MD_DIR / fname).read_text(encoding="utf-8")
    found = fs._scan_subitem_rows(text, "2026.2Q")
    print(f"{code}: _scan_subitem_rows found = {found}")
