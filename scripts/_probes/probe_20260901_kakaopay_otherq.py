# -*- coding: utf-8 -*-
import sys, io
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
for pdf_path in sorted((ROOT/"data"/"disclosure").glob("*/raw/KR1098_*.pdf")):
    doc = fitz.open(str(pdf_path))
    total_chars = sum(len(doc[p].get_text()) for p in range(len(doc)))
    print(f"{pdf_path.parent.parent.name}: pages={len(doc)} total_chars={total_chars}")
    if total_chars > 500:
        for pno in range(len(doc)):
            t = doc[pno].get_text()
            if "비례성원칙" in t or "관계회사" in t or "종속회사" in t or "기타요구자본" in t:
                print(f"    hit page {pno+1}: {t[:80]!r}")
    doc.close()
