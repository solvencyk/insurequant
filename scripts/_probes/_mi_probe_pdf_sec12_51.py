"""Diagnostic: locate 1-2 (경영효율지표) and 5-1 (수익성, with 투자이익/경과운용자산) tables in raw PDF
for companies whose MD lacked them. Read-only.
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"

TARGETS = [
    "KR0004_MG_예별손해보험", "KR0009_현대해상", "KR0032_NH농협손해보험",
    "KR0082_DB생명보험", "KR0099_케이비라이프생명보험", "KR0104_농협생명보험",
    "KR0087_동양생명", "KR0080_에이아이에이생명보험",
]


def find_page(doc, needle_variants, start=0):
    for pno in range(start, len(doc)):
        t = doc[pno].get_text().replace(" ", "")
        for nv in needle_variants:
            if nv in t and "..." not in doc[pno].get_text()[:200]:
                # skip obvious TOC pages (lots of dot leaders)
                dots = doc[pno].get_text().count(".")
                if dots > 80:
                    continue
                return pno
    return None


for stem in TARGETS:
    pdf_path = PDF_DIR / f"{stem}.pdf"
    if not pdf_path.exists():
        print(f"{stem}: PDF NOT FOUND")
        continue
    doc = fitz.open(str(pdf_path))
    p12 = find_page(doc, ["1-2.주요경영효율지표", "주요경영효율지표"], start=2)
    p51 = find_page(doc, ["5-1.수익성", "투자이익(A)", "경과운용자산(B)"], start=2)
    print(f"\n=== {stem} (pages={len(doc)}) 1-2@page={p12+1 if p12 is not None else None} 5-1@page={p51+1 if p51 is not None else None} ===")
    if p12 is not None:
        print("--- 1-2 text ---")
        print(doc[p12].get_text()[:1400])
    if p51 is not None and p51 != p12:
        print("--- 5-1 text ---")
        print(doc[p51].get_text()[:1200])
    doc.close()
