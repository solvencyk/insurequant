# -*- coding: utf-8 -*-
"""READ-ONLY pass2 r02 (KR0079): in an era-2 (원 wide, product columns) filing print the row '보험수익, 비금융위험에 대한 위험조정의 변동분' (and the CSM-recognition row) of every separate-notes table:
physical lines, the 당기/전기 block it sits in, the numeric cells and their row sum (원 -> 백만원).  usage: r02_mirae_era2_rows.py FY2025_Q2 [FY..]"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
for fy in sys.argv[1:]:
    path, lines, s0, tabs = P.tables_with("KR0079", fy, ["보험수익,비금융위험에대한위험조정의변동분"])
    print(f"##### {fy} {P.M.rel(path)} sep start L{s0}: {len(tabs)} tables")
    for t, rows in tabs:
        print(f"  --- table@L{t['start']}-{t['end']} caption={P.nl(t['caption'] or '')[:50]!r}")
        hdr = [P.rowtext(r) + "|" + (r["cells"][1]["text"] if len(r["cells"]) > 1 else "") for r in rows[:7]]
        print("      hdr:", " // ".join(h[:60] for h in hdr if h.strip("|")))
        blk = None
        for r in rows:
            L = P.lab(r)
            first2 = P.nl(" ".join(c["text"] for c in r["cells"][:2]))
            if L in ("당기", "당분기", "당반기", "전기", "전분기", "전반기") or first2 in ("당기", "당분기", "당반기", "전기", "전분기", "전반기"):
                blk = first2
            if "보험수익,비금융위험에대한위험조정의변동분" in first2 or "보험수익,서비스의이전" in first2 or "보험수익,보험계약서비스의이전" in first2:
                n = P.nums(r, skip=1)
                s = sum(v for v, _l, _t in n)
                print(f"      [{blk}] R{r['tr_line']} {first2[:60]:60s} n={len(n)} sum(원)={s:,.0f} (백만원 {s / 1e6:,.3f}) first={n[0][2] if n else None}@{n[0][1] if n else None}")
