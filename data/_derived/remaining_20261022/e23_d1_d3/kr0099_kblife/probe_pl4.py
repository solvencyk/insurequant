# -*- coding: utf-8 -*-
"""KR0099 probe (read-only): the KB라이프 prior-period 보험영업수익 note table (item 4 source) of the three FY2024 quarterly filings, all rows with all cells."""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife")
import e23_read as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, W, M, nl = X.T, X.W, X.M, X.nl
for q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    fy = M.later_fy(q)
    path = T.main_path("KR0099", fy)
    lines, s0, tabs = X.tables_sep(path)
    print("=" * 100)
    print(q, M.rel(path), "sep notes start L", s0)
    for t, rows in tabs:
        cap = nl(t["caption"] or "")
        if "기타사업비용을제외한" not in cap or "보험영업수익" not in cap:
            continue
        hdr = nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        print("-- table@L%d caption=%r hdr=%r unit=%s" % (t["start"], t["caption"], hdr[:80], T.find_unit(lines, t, span=2500)))
        for r in rows[:40]:
            lab_ = X.lab(r)
            if "보험계약마진" in lab_ or lab_.startswith("구분") or lab_ in ("보험영업수익", "보험영업비용"):
                print("   ", [(c["text"], c["line"]) for c in r["cells"]])
