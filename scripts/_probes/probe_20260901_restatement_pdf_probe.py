# -*- coding: utf-8 -*-
"""3사(메리츠·NH농협손보·삼성생명)의 docling MD 에 적용전 세부표가 없다.
raw PDF 에 텍스트로 있는지(=스캔이 아닌지) 먼저 확인한다.
'키워드 0회 = 원문 없음' 으로 단정하지 않기 위한 절차.
"""
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"

TARGETS = ["KR0001_메리츠화재해상보험", "KR0032_NH농협손해보험", "KR0069_삼성생명"]


def main():
    for name in TARGETS:
        p = PDF / f"{name}.pdf"
        doc = fitz.open(p)
        print("=" * 90)
        print(f"{name}  pages={doc.page_count}")
        hits = []
        for pno in range(doc.page_count):
            t = doc[pno].get_text()
            if "지급여력기준금액" in t and "분산효과" in t:
                hits.append(pno)
        print("  pages with 지급여력기준금액+분산효과:", [h + 1 for h in hits])
        for pno in hits[:2]:
            t = doc[pno].get_text()
            print(f"  --- p{pno+1} (chars={len(t)}) ---")
            print(t[:2200])
        if not hits:
            dens = [(pno + 1, len(doc[pno].get_text())) for pno in range(doc.page_count)]
            print("  no hit; per-page text density:", dens)
        doc.close()


if __name__ == "__main__":
    sys.exit(main())
