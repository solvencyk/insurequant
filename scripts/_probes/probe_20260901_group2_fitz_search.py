# -*- coding: utf-8 -*-
"""fitz-based keyword search across full PDF for ambiguous group2 buckets.
Read-only. Finds pages containing '비례성원칙' or '관계회사' and dumps text."""
import sys, io
from pathlib import Path
import fitz  # PyMuPDF
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

TARGETS = [
    ("KR0049", "악사손해보험", "FY2024_Q4"),
    ("KR0049", "악사손해보험", "FY2025_Q1"),
    ("KR1098", "카카오페이손해보험", "FY2024_Q4"),
    ("KR0003", "롯데손해보험", "FY2026_Q1"),
]

def find_pdf(code, period):
    d = ROOT / "data" / "disclosure" / period / "raw"
    if not d.is_dir():
        return None
    matches = list(d.glob(f"{code}_*.pdf"))
    return matches[0] if matches else None

for code, name, period in TARGETS:
    print(f"\n{'='*100}")
    print(f"### {code} {name} {period}")
    pdf_path = find_pdf(code, period)
    if pdf_path is None:
        print("  [NO PDF FOUND]")
        continue
    print(f"  file: {pdf_path.relative_to(ROOT)}")
    doc = fitz.open(str(pdf_path))
    print(f"  pages: {len(doc)}")
    for pno in range(len(doc)):
        page = doc[pno]
        text = page.get_text()
        if "비례성원칙" in text or "관계회사" in text or "종속회사" in text:
            print(f"\n  --- page {pno+1} (chars={len(text)}) ---")
            # find context around the keyword
            for kw in ("비례성원칙", "종속회사", "관계회사"):
                idx = text.find(kw)
                if idx >= 0:
                    lo = max(0, idx - 100)
                    hi = min(len(text), idx + 300)
                    print(f"  [{kw} @ {idx}]: ...{text[lo:hi]!r}...")
    doc.close()
