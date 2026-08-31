# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
import fill_market_subitems_to_disclosure as fm
from pathlib import Path

MD = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\md_inbox\FY2026_Q2\KR0069_삼성생명.md")
text = MD.read_text(encoding="utf-8")
subs = fm.extract_mkt_subs(text)
print("extract_mkt_subs raw output:", subs)
for item_no, (val, unit) in subs.items():
    eok = fm._to_eok(val, unit)
    print(f"  item{item_no}: raw={val!r} unit={unit} -> {eok} 억원")

print()
pdf_dir = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\raw")
pdf_dir_fb = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf")
import glob
pdfs = sorted(glob.glob(str(pdf_dir / "KR0069_*.pdf")))
print("raw/ matches:", pdfs)
if not pdfs:
    pdfs = sorted(glob.glob(str(pdf_dir_fb / "KR0069_*.pdf")))
print("pdf/ fallback matches:", pdfs)
if pdfs:
    vals, total = fm.extract_irr_netassets(pdfs[0])
    print("extract_irr_netassets vals:", vals, "total:", total)
