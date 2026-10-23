# -*- coding: utf-8 -*-
"""KR0099 probe (read-only): all row labels of the prior-period 보험영업수익 note table (rows that carry numbers) for the FY2024 Q1 filing."""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife")
import e23_read as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, W, M, nl = X.T, X.W, X.M, X.nl
q = sys.argv[1]
fy = M.later_fy(q)
path = T.main_path("KR0099", fy)
lines, s0, tabs = X.tables_sep(path)
import re
for t, rows in tabs:
    cap = nl(t["caption"] or "")
    if "기타사업비용을제외한" not in cap or "보험영업수익" not in cap:
        continue
    hdr = nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
    which = "PRIOR" if re.search(r"구분(전분기|전반기|전기)", hdr) else "CUR"
    print("-- table@L%d %s rows=%d" % (t["start"], which, len(rows)))
    for r in rows:
        print("    L%s %-60s %s" % (r["cells"][0]["line"], X.lab(r), [c["text"] for c in r["cells"][1:]]))
