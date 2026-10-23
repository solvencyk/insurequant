# -*- coding: utf-8 -*-
"""READ-ONLY pass2 r01 (KR0068 한화생명): list the separate-notes LOB note tables (구분 사망/건강/연금저축/변액/기타/합계) with a 위험해제 RA row: caption, line range, unit and the 합계 of the RA row."""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P
sys.stdout.reconfigure(encoding="utf-8")
for fy in sys.argv[1:]:
    path, lines, s0, tabs = P.tables_with("KR0068", fy, ["위험해제에따른위험조정의변동", "서비스제공에따른보험계약마진의변동"])
    print("#####", fy, P.M.rel(path), "sep start", s0, "tables", len(tabs))
    for t, rows in tabs:
        hdr = P.nl(" ".join(c["text"] for r in rows[:4] for c in r["cells"]))
        r5 = [r for r in rows if "위험해제에따른위험조정의변동" in P.lab(r)]
        n = P.nums(r5[0]) if r5 else []
        print(f"  table@L{t['start']}-{t['end']} caption={P.nl(t['caption'] or '')[:40]!r} unit={P.T.find_unit(lines, t, span=2500)} hdr={hdr[:50]!r} RA row: " + " | ".join(f"{x[2]}@{x[1]}" for x in n))
