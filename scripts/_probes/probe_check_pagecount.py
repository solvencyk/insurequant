import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq
import fitz

pairs = [
    ("KR0079", "FY2024_Q4"), ("KR0080", "FY2024_Q4"), ("KR0097", "FY2024_Q4"),
    ("KR0079", "FY2025_Q4"), ("KR0080", "FY2025_Q4"), ("KR0079", "FY2023_Q4"),
]
for code, period in pairs:
    pdf_path = aq.find_pdf(period, code)
    if pdf_path is None:
        print(f"{code} {period}: NOT FOUND")
        continue
    doc = fitz.open(pdf_path)
    n = len(doc)
    has_anchor = any("가중부실자산" in doc[i].get_text() for i in range(n))
    doc.close()
    import os
    size = os.path.getsize(pdf_path)
    print(f"{code} {period}: pages={n} size={size/1e6:.1f}MB has_가중부실자산={has_anchor} path={pdf_path.name}")
