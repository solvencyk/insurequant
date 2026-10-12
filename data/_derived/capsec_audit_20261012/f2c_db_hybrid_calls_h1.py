# -*- coding: utf-8 -*-
"""f2c: print the DB손해보험 FY2026 반기보고서 text around '발행일로부터 5년' / '중도상환' / '조기상환' (hybrid terms) to see the printed call dates of 제1회/제2회. Read-only."""
import re

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
fn = ROOT + "/data/dart/FY2026_Q2/raw/KR0011_DB손해보험/20260814003682.xml"
txt = open(fn, encoding="utf-8", errors="replace").read()
clean = re.sub(r"<[^>]+>", " ", txt)
clean = re.sub(r"\s+", " ", clean)
for pat in ["발행일로부터 5년", "중도상환 가능", "조기상환가능일", "만기 및 조기상환"]:
    hits = [m.start() for m in re.finditer(re.escape(pat), clean)]
    print("==", pat, "hits", len(hits))
    for h in hits[:6]:
        print("    ...", clean[max(0, h - 230): h + 200])
