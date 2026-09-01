# -*- coding: utf-8 -*-
"""스캔 PDF 5사의 '적용 전 지급여력비율 세부' 표 페이지를 렌더링한다.

텍스트레이어가 없다고 '원문 없음' 으로 단정하지 않는다(저장소 규율:
keyword absence != source absence). 240dpi 로 뽑아 육안 판독한다.
페이지는 docling MD 가 알려주는 표 순서를 못 쓰므로 후보 범위를 통째로 뽑는다.
"""
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "data" / "disclosure"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

JOBS = [
    ("FY2026_Q1", "KR0010"), ("FY2026_Q2", "KR0010"),
    ("FY2026_Q1", "KR0049"),
    ("FY2026_Q1", "KR0079"), ("FY2026_Q2", "KR0079"),
    ("FY2026_Q1", "KR0080"),
    ("FY2026_Q1", "KR0087"), ("FY2026_Q2", "KR0087"),
]
RANGE = range(12, 25)          # 0-idx; 실측상 표는 14~22p 사이


def find_pdf(period, code):
    for sub in ("pdf", "raw"):
        d = DISC / period / sub
        if d.is_dir():
            hits = sorted(d.glob(f"{code}_*.pdf"))
            if hits:
                return hits[0]
    return None


def main():
    for period, code in JOBS:
        p = find_pdf(period, code)
        if p is None:
            print("MISSING", period, code)
            continue
        doc = fitz.open(p)
        print(f"{code} {period} -> {p.name} pages={doc.page_count}")
        for pno in RANGE:
            if pno >= doc.page_count:
                break
            pix = doc[pno].get_pixmap(dpi=150)
            f = OUT / f"{code}_{period}_p{pno+1:02d}.png"
            pix.save(f)
        doc.close()
    print("wrote to", OUT)


if __name__ == "__main__":
    sys.exit(main())
