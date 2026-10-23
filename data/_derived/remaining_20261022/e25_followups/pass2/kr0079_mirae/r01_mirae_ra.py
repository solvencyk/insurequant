# -*- coding: utf-8 -*-
"""READ-ONLY pass2 r01 (KR0079 미래에셋): for each filing, list every separate-notes table that has a 위험조정 변동분 row, with caption, the RA row cells (physical lines) and the CSM-recognition row.
usage: r01_mirae_ra.py FY2024_Q1 [FY..]"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
for fy in sys.argv[1:]:
    path, lines, s0, tabs = P.tables_with("KR0079", fy, ["위험조정변동분"])
    print(f"##### {fy} {P.M.rel(path)} sep start L{s0}: {len(tabs)} tables with a 위험조정 변동분 row")
    for t, rows in tabs:
        u = P.T.find_unit(lines, t, span=2500)
        print(f"  --- table@L{t['start']}-{t['end']} unit={u} caption={P.nl(t['caption'] or '')[:50]!r}")
        blk = None
        for r in rows:
            L = P.lab(r)
            if L in ("당기", "당분기", "당반기", "전기", "전분기", "전반기", "당기말", "전기말"):
                blk = L
            if "위험조정변동분" in L or L.startswith("서비스의이전으로당기손익에인식한보험계약마진") or "보험계약서비스의이전" in L:
                n = P.nums(r)
                print(f"    [{blk}] R{r['tr_line']} {P.rowtext(r)[:34]:34s} " + " | ".join(f"{tx}@{ln}" for _v, ln, tx in n))
