# -*- coding: utf-8 -*-
"""f2b: grep DB손해보험 FY2025 사업보고서 raw for the call dates (2030.09.xx / 2030-09-xx) of the two 2025 hybrids. Read-only."""
import glob
import re

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
for fn in sorted(glob.glob(ROOT + "/data/dart/FY2025_Q4/raw/KR0011_*/*.xml")):
    txt = open(fn, encoding="utf-8", errors="replace").read()
    clean = re.sub(r"<[^>]+>", " ", txt)
    clean = re.sub(r"\s+", " ", clean)
    print("==", fn.replace(ROOT + "/", ""), len(clean))
    for pat in ["2030.09", "2030-09", "2030년 9월", "콜옵션", "조기상환"]:
        hits = [m.start() for m in re.finditer(re.escape(pat), clean)]
        print("  ", pat, "hits", len(hits))
        for h in hits[:3]:
            print("      ...", clean[max(0, h - 200): h + 260])
