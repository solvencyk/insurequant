# -*- coding: utf-8 -*-
"""READ-ONLY pass3 d10 (KR0087 동양생명): dump every separate-basis note table of the given filing that mentions 재보험 + (보험계약마진 | 위험조정 | 예상 | 실제), with physical xml line numbers.
usage: d10_dy_reins_dump.py FYxxxx_Qn [needle ...]    (default needles: 재보험)"""
import os
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2")
import p2lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fy = sys.argv[1]
needles = sys.argv[2:] or ["재보험"]
path, lines, s0, tabs = P.tables_with("KR0087", fy, needles)
print(f"##### KR0087 {fy} {P.M.rel(path)} separate notes start L{s0}; {len(tabs)} tables with {needles}")
for t, rows in tabs:
    unit = P.T.find_unit(lines, t, span=2500)
    blob = P.nl(" ".join(c["text"] for r in rows for c in r["cells"][:2]))
    if not os.environ.get("DUMP_ALL") and not any(k in blob for k in ("보험계약마진", "위험조정", "예상", "실제")):
        continue
    print(f"--- table@L{t['start']}-{t['end']} unit={unit} title={t['title']!r} caption={P.nl(t['caption'] or '')[:90]!r} rows={len(rows)}")
    for r in rows:
        if not r["cells"]:
            continue
        n = P.nums(r, skip=0)
        txt = " | ".join(f"{c['text']}@{c['line']}" for c in r["cells"][:8])
        print(f"   R{r['tr_line']:>6} {txt[:230]}")
