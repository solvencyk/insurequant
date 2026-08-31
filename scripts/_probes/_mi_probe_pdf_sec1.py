"""Diagnostic: for companies whose MD lacks section 1-1/1-2 or 5-1, check whether the raw PDF
has extractable text (not scanned) on the pages where those sections should live, and print a
sample of the text so we can judge table-layout feasibility for a PDF-fallback extractor.
Read-only (fitz open, no writes).
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"

# companies missing section-1 content in MD (from survey v2)
MISSING_SEC1 = [
    "KR0001_메리츠화재해상보험", "KR0002_한화손해보험", "KR0004_MG_예별손해보험",
    "KR0005_흥국화재", "KR0008_삼성화재해상보험", "KR0009_현대해상",
    "KR0029_AIG손해보험", "KR0032_NH농협손해보험", "KR0051_신한이지손해보험",
    "KR0068_한화생명", "KR0070_에이비엘생명보험", "KR0071_흥국생명보험",
    "KR0072_케이디비생명보험", "KR0074_라이나생명보험", "KR0080_에이아이에이생명보험",
    "KR0082_DB생명보험", "KR0087_동양생명", "KR0094_신한라이프생명보험",
    "KR0097_하나생명보험", "KR0104_농협생명보험", "KR1000_코리안리재보험",
    "KR1010_교보라이프플래닛생명보험",
]

for stem in MISSING_SEC1:
    pdf_path = PDF_DIR / f"{stem}.pdf"
    if not pdf_path.exists():
        print(f"{stem}: PDF NOT FOUND")
        continue
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"{stem}: OPEN FAIL {e}")
        continue
    n = len(doc)
    # scan first 6 pages for the keyword and char density
    hit_page = None
    for pno in range(min(6, n)):
        page = doc[pno]
        text = page.get_text()
        if "주요 경영지표" in text.replace(" ", "") or "주요경영지표" in text.replace(" ", ""):
            hit_page = pno
            break
    p0_len = len(doc[0].get_text()) if n > 0 else 0
    print(f"\n=== {stem} (pages={n}, p1_chars={p0_len}, hit_page={hit_page + 1 if hit_page is not None else None}) ===")
    if hit_page is not None:
        txt = doc[hit_page].get_text()
        print(txt[:1500])
    else:
        # dump page1 first 400 chars to see what's there instead
        print("[NO '주요경영지표' HIT IN PAGES 1-6] page1 sample:")
        print((doc[0].get_text() if n > 0 else "")[:400])
    doc.close()
