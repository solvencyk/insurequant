# -*- coding: utf-8 -*-
"""READ-ONLY: list captions/line ranges of the 구분 장기 자동차 일반 합계 note tables with a 보험계약마진상각 row (FY2024_Q2 / FY2024_Q3) to locate the 3-month tables."""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P
sys.stdout.reconfigure(encoding="utf-8")
for fy in sys.argv[1:]:
    path, lines, s0, tabs = P.load("KR0009", fy)
    print("#####", fy, P.M.rel(path))
    for t, rows in tabs:
        hdr = P.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        labs = [P.lab(r) for r in rows]
        if hdr.startswith("구분장기자동차일반합계") and "보험계약마진상각" in labs and "위험조정변동" in labs:
            r5 = [r for r in rows if P.lab(r) == "위험조정변동"][0]
            n = P.nums(r5)
            print(f"  table@L{t['start']}-{t['end']} caption={t['caption']!r} unit={P.T.find_unit(lines, t, span=2500)} 장기 RA={n[0][2]}@{n[0][1]}")
