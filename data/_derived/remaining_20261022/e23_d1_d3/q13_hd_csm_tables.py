# -*- coding: utf-8 -*-
"""e23 probe (read-only): 현대해상 FY2024 filings -- all separate-notes tables that look like a BEL/RA/CSM roll-forward (rows 기초순보험계약부채 + 기말보험계약순부채), with caption, header and the CSM column opening / closing."""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as X  # noqa: E402
import e21_raw as W  # noqa: E402
import e21_t2 as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
nl = T.nl
code = sys.argv[1] if len(sys.argv) > 1 else "KR0009"
fys = sys.argv[2:] or ["FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"]
for fy in fys:
    for path in X.M.main_xmls(code, fy):
        lines, s0, tabs = X.tables_sep(path)
        print("#" * 90)
        print(X.M.rel(path), "sep start", s0)
        for t, rows in tabs:
            labs = [X.lab(r) for r in rows]
            if "기초순보험계약부채" not in labs or "신계약효과" not in labs or "보험계약마진합계" not in nl(" ".join(c["text"] for r in rows[:2] for c in r["cells"])):
                continue
            hdr = nl(" ".join(c["text"] for r in rows[:2] for c in r["cells"]))[:70]
            op = [r for r in rows if X.lab(r) == "기초순보험계약부채"]
            cl = [r for r in rows if X.lab(r) in ("기말보험계약순부채", "당기말보험계약순부채")]
            opv = W.numeric_cells(op[0])[2][2] if op and len(W.numeric_cells(op[0])) > 2 else None
            clv = W.numeric_cells(cl[0])[2][2] if cl and len(W.numeric_cells(cl[0])) > 2 else None
            print(f"  L{t['start']}-{t['end']} cap={t['caption'][:44]!r} hdr={hdr!r} nrows={len(rows)} open_csm={opv} close_csm={clv}")
            pass
