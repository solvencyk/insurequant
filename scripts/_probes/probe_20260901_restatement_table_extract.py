# -*- coding: utf-8 -*-
"""적용전 세부표를 raw PDF 에서 좌표로 추출하는 실험 (39사 중 3사로 형태 확인).

docling MD 는 회사에 따라 표를 쪼개거나(KR0079/KR0087) 숫자를 붙여 버려서
(KR0010 '155,3161') 그대로 쓰면 오탐이 난다. PDF 좌표가 정본이다.
"""
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"

NUM_RE = re.compile(r"^[\(\[]?[-△▲]?[\d,]+(?:\.\d+)?[\)\]]?%?$")


def find_page(doc):
    for pno in range(doc.page_count):
        t = doc[pno].get_text()
        if "분산효과" in t and "지급여력기준금액" in t and "기본요구자본" in t:
            return pno
    return None


def rows_from_page(page):
    words = page.get_text("words")
    if not words:
        return []
    # y 클러스터 (같은 줄)
    words = sorted(words, key=lambda w: (round(w[1], 1), w[0]))
    lines = []
    for w in words:
        yc = (w[1] + w[3]) / 2
        if lines and abs(lines[-1][0] - yc) <= 3.0:
            lines[-1][1].append(w)
        else:
            lines.append([yc, [w]])
    out = []
    for yc, ws in lines:
        ws = sorted(ws, key=lambda w: w[0])
        out.append((yc, ws))
    return out


def main():
    for name in ["KR0001_메리츠화재해상보험", "KR0010_KB손해보험", "KR0079_미래에셋생명"]:
        doc = fitz.open(PDF / f"{name}.pdf")
        pno = find_page(doc)
        print("=" * 90)
        print(name, "page", (pno + 1) if pno is not None else None)
        if pno is None:
            continue
        page = doc[pno]
        print("  page width", page.rect.width)
        for yc, ws in rows_from_page(page):
            lbl = " ".join(w[4] for w in ws if not NUM_RE.match(w[4]))
            nums = [(round((w[0] + w[2]) / 2, 1), w[4]) for w in ws if NUM_RE.match(w[4])]
            if lbl.strip() or nums:
                print(f"   y={yc:7.1f} | {lbl[:52]:52s} | {nums}")
        doc.close()


if __name__ == "__main__":
    sys.exit(main())
