"""Read-only: locate the measurement-model table (ILP items 1-8, 억원) in the FY2025_Q4 Kyobo disclosure PDF and print the 합계 numbers."""
import sys, re
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import fitz
from _disclosure_pdf_paths import latest_disclosure_pdfs, disclosure_pdfs
for per in ("FY2025_Q4",):
    for p in disclosure_pdfs(per, "KR0073"):
        doc = fitz.open(str(p))
        print("##", per, p.name, "pages", len(doc))
        for i, pg in enumerate(doc, 1):
            t = pg.get_text()
            if "회계모형별" in t and "포트폴리오별" in t:
                lines = [l for l in t.split("\n") if l.strip()]
                print("--- page", i, "nlines", len(lines))
                print("|".join(lines[:6]))
                # print tail (합계 rows)
                print("TAIL:", "|".join(lines[-60:]))
