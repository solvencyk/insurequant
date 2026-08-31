# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz
from pathlib import Path
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
import fill_market_subitems_to_disclosure as fm

PDF_DIR = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")
doc = fitz.open(PDF_DIR / "KR0070_에이비엘생명보험.pdf")
t = doc[30].get_text()
print("--- ABL page 31 FULL ---")
print(t)
doc.close()

print()
for code, fname in [("KR0070", "KR0070_에이비엘생명보험.md"), ("KR0082", "KR0082_DB생명보험.md")]:
    md = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\md_inbox\FY2026_Q2") / fname
    subs = fm.extract_mkt_subs(md.read_text(encoding="utf-8"))
    print(f"{code} extract_mkt_subs:", subs)
